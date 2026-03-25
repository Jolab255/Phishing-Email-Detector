from app import app, db
import threading
import time
import os
from app.gmail_service import get_gmail_service
from app.phishing_detector_model import analyze_email
from app.alert_system import play_alert_sound
from app.models import AnalyzedEmail
import base64

def check_for_new_emails():
    """Checks for new emails and plays an alert if a phishing email is found."""
    print("Initializing Gmail service...")
    service = get_gmail_service()
    if service is None:
        print("Failed to get Gmail service. Exiting email checker thread.")
        return
    
    print("Gmail service initialized successfully. Starting email monitoring...")
    
    # Keep track of the most recent message ID we've seen
    most_recent_message_id = None
    
    # Monitor for new incoming messages
    print("Monitoring for new incoming messages...")
    processed_message_ids = set()  # Keep track of processed messages to avoid duplicates
        
    while True:
        try:
            print("Checking for new emails...")
            # Get messages sorted by date (newest first)
            results = service.users().messages().list(
                userId='me', 
                labelIds=['INBOX'],
                maxResults=5
            ).execute()
            messages = results.get('messages', [])
            print(f"Found {len(messages)} recent messages")
            
            if messages:
                # Check if we have a new most recent message
                newest_message_id = messages[0]['id']
                
                # If this is our first run or we have a new message
                if most_recent_message_id is None or newest_message_id != most_recent_message_id:
                    print(f"New messages detected. Most recent message ID: {newest_message_id}")
                    most_recent_message_id = newest_message_id
                    
                    # Process all new messages
                    for message in messages:
                        message_id = message['id']
                        
                        # Skip if we've already processed this message
                        if message_id in processed_message_ids:
                            continue
                        
                        print(f"Processing new message ID: {message_id}")
                        processed_message_ids.add(message_id)
                        
                        # Check if the email has been seen before
                        msg = service.users().messages().get(userId='me', id=message_id).execute()
                        if 'UNREAD' in msg['labelIds']:
                            print("Message is unread, processing...")
                            payload = msg['payload']
                            if 'parts' in payload:
                                parts = payload['parts']
                                data = parts[0]['body']['data']
                            else:
                                data = payload['body']['data']
                            
                            text = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
                            print(f"Background check - Email content length: {len(text)}")
                            
                            result, confidence, features, reasoning, risk_factors, safety_score = analyze_email(text)
                            print(f"Background check - Analysis result: {result}, Confidence: {confidence}")
                            
                            # Save the analysis result to the database
                            with app.app_context():
                                email = AnalyzedEmail.query.filter_by(email_id=message_id).first()
                                
                                import json
                                risk_factors_json = json.dumps(risk_factors)
                                safety_score_json = json.dumps(safety_score)
                                
                                if not email:
                                    # Extract sender and subject for database storage
                                    try:
                                        msg_details = service.users().messages().get(
                                            userId='me', 
                                            id=message_id, 
                                            format='metadata', 
                                            metadataHeaders=['From', 'Subject']
                                        ).execute()
                                        
                                        sender = ""
                                        subject = ""
                                        for header in msg_details['payload']['headers']:
                                            if header['name'] == 'From':
                                                sender = header['value']
                                            elif header['name'] == 'Subject':
                                                subject = header['value']
                                    except Exception as e:
                                        print(f"Error fetching message details for database: {e}")
                                        sender = ""
                                        subject = ""
                                    
                                    email = AnalyzedEmail(
                                        email_id=message_id, 
                                        sender=sender, 
                                        subject=subject, 
                                        result=result, 
                                        score=confidence,
                                        reasoning=reasoning,
                                        risk_factors=risk_factors_json,
                                        safety_score=safety_score_json
                                    )
                                    db.session.add(email)
                                    db.session.commit()
                                    print(f"Saved new analysis result to database for message {message_id}: Result={result}, Confidence={confidence}")
                                else:
                                    # Update existing record
                                    old_result = email.result
                                    old_score = email.score
                                    email.result = result
                                    email.score = confidence
                                    email.reasoning = reasoning
                                    email.risk_factors = risk_factors_json
                                    email.safety_score = safety_score_json
                                    db.session.commit()
                                    print(f"Updated analysis result in database for message {message_id}: Result={old_result} -> {result}, Confidence={old_score} -> {confidence}")
                            
                            if result == 'PHISHING':
                                print("PHISHING EMAIL DETECTED! Playing alert sound...")
                                play_alert_sound()
                            
                            # Mark the email as read
                            service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}).execute()
                            print("Message marked as read")
                        else:
                            print("Message is already read, skipping...")
            else:
                print("No messages found")
        except Exception as e:
            print(f"Error checking for emails: {e}")
            import traceback
            traceback.print_exc()
            
        print("Waiting 30 seconds before next check...")
        time.sleep(30)

if __name__ == '__main__':
    # Allow OAuth over HTTP for local development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    print("Starting Phishing Detector...")
    print("If this is your first time running the application, you'll need to authenticate with Gmail.")
    print("Make sure your Google account has been added as a test user in the Google Cloud Console.")
    print("If you encounter authentication errors, please check the Google Cloud Console settings.")
    
    # Start the background thread immediately
    print("Starting background email checker thread...")
    checker_thread = threading.Thread(target=check_for_new_emails)
    checker_thread.daemon = True
    checker_thread.start()
    print("Background email checker thread started")
    
    # Start Flask app on port 5000
    app.run(debug=True, use_reloader=False, port=5000, host='127.0.0.1')