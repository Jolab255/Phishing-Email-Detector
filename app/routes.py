from app import app, db
from flask import render_template, redirect, url_for, request, flash, session
from flask_login import current_user, login_user, logout_user, login_required
from app.gmail_service import get_gmail_service, get_auth_flow
from app.phishing_detector_model import analyze_email
from app.utils import smart_format_reasoning
from app.models import AnalyzedEmail, User
import base64
import json
import os
from urllib.parse import urlparse

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if request.form['password'] != request.form['confirm_password']:
            flash('Passwords do not match!')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        user = User(username=request.form['username'], email=request.form['email'])
        user.set_password(request.form['password'])
        user.set_secret_answer(request.form['secret_answer'])
        
        if User.query.count() == 0:
            user.is_verified = True
            user.is_admin = True
            
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if not user:
            flash('User not found.')
            return redirect(url_for('reset_password'))
        if not user.check_secret_answer(request.form['secret_answer']):
            flash('Incorrect security answer.')
            return redirect(url_for('reset_password'))
        if request.form['new_password'] != request.form['confirm_new_password']:
            flash('Passwords do not match!')
            return redirect(url_for('reset_password'))
        user.set_password(request.form['new_password'])
        db.session.commit()
        flash('Password has been reset successfully!')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password')

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Permission denied.')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/verify/<int:user_id>')
@login_required
def verify_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    user = User.query.get(user_id)
    if user:
        user.is_verified = not user.is_verified
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- WEB AUTH FLOW ROUTES ---
@app.route('/link_gmail')
@login_required
def link_gmail():
    if not current_user.is_verified:
        flash("You must be verified first.")
        return redirect(url_for('index'))
    
    # We use 127.0.0.1:5000 as the callback URL for local dev
    # This MUST match the Redirect URI in Google Cloud Console
    redirect_uri = url_for('oauth2callback', _external=True)
    flow = get_auth_flow(redirect_uri)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
@login_required
def oauth2callback():
    state = session.get('oauth_state')
    redirect_uri = url_for('oauth2callback', _external=True)
    flow = get_auth_flow(redirect_uri)
    flow.fetch_token(authorization_response=request.url)
    
    if not os.path.exists('tokens'):
        os.makedirs('tokens')
        
    token_path = f'tokens/token_{current_user.id}.json'
    creds = flow.credentials
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
        
    flash("Gmail linked successfully!")
    return redirect(url_for('index'))
# ----------------------------

@app.route('/refresh_messages')
@login_required
def refresh_messages():
    if not current_user.is_verified:
        return render_template('messages_list.html', messages=[], error="Verification needed.")
    
    service = get_gmail_service()
    if service is None:
        return render_template('messages_list.html', messages=[], needs_link=True)
        
    try:
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
        messages = results.get('messages', [])
        enriched_messages = []
        for message in messages:
            try:
                msg = service.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
                sender = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'From'), "Unknown")
                subject = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'Subject'), "No Subject")
                date = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'Date'), "")
                enriched_messages.append({'id': message['id'], 'sender': sender, 'subject': subject, 'date': date})
            except:
                enriched_messages.append({'id': message['id'], 'sender': 'Unknown', 'subject': 'Error', 'date': ''})
    except:
        enriched_messages = []
    return render_template('messages_list.html', messages=enriched_messages)

@app.route('/')
@app.route('/index')
@login_required
def index():
    if not current_user.is_verified:
        return render_template('index.html', title='Home', messages=[], verification_needed=True)
                             
    service = get_gmail_service()
    if service is None:
        return render_template('index.html', title='Home', messages=[], needs_gmail_link=True)
        
    try:
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
        messages = results.get('messages', [])
        enriched_messages = []
        for message in messages:
            try:
                msg = service.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
                sender = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'From'), "Unknown")
                subject = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'Subject'), "No Subject")
                date = next((h['value'] for h in msg['payload']['headers'] if h['name'] == 'Date'), "")
                enriched_messages.append({'id': message['id'], 'sender': sender, 'subject': subject, 'date': date})
            except:
                enriched_messages.append({'id': message['id'], 'sender': 'Unknown', 'subject': 'Error', 'date': ''})
    except:
        enriched_messages = []
    return render_template('index.html', title='Home', messages=enriched_messages)

@app.route('/analyze/<message_id>')
@login_required
def analyze(message_id):
    email = AnalyzedEmail.query.filter_by(email_id=message_id, user_id=current_user.id).first()
    if email and email.reasoning and email.result != 'ERROR':
        try:
            risk_factors = json.loads(email.risk_factors) if email.risk_factors else []
            safety_score = json.loads(email.safety_score) if email.safety_score else {}
        except:
            risk_factors, safety_score = [], {}
        return render_template('analysis.html', title='Analysis', 
                             result=email.result, confidence=email.score,
                             reasoning=smart_format_reasoning(email.reasoning), 
                             risk_factors=risk_factors, safety_score=safety_score,
                             sender=email.sender, subject=email.subject, 
                             content=email.content[:500] + "...")

    try:
        service = get_gmail_service()
        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = msg['payload']
        sender = next((h['value'] for h in payload['headers'] if h['name'] == 'From'), "Unknown")
        subject = next((h['value'] for h in payload['headers'] if h['name'] == 'Subject'), "Unknown")
        
        data = ""
        if 'parts' in payload:
            data = payload['parts'][0]['body'].get('data', '')
        else:
            data = payload['body'].get('data', '')
            
        text = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8') if data else ""
        result, confidence, features, reasoning, risk_factors, safety_score = analyze_email(text)
        
        if not email:
            email = AnalyzedEmail(
                email_id=message_id, user_id=current_user.id, sender=sender, subject=subject, 
                result=result, score=confidence, reasoning=reasoning,
                risk_factors=json.dumps(risk_factors), safety_score=json.dumps(safety_score),
                content=text
            )
            db.session.add(email)
        else:
            email.result, email.score, email.reasoning = result, confidence, reasoning
            email.risk_factors, email.safety_score, email.content = json.dumps(risk_factors), json.dumps(safety_score), text
        db.session.commit()
        
        return render_template('analysis.html', title='Analysis', 
                             result=result, confidence=confidence, 
                             reasoning=smart_format_reasoning(reasoning), 
                             risk_factors=risk_factors, safety_score=safety_score,
                             sender=sender, subject=subject, content=text[:500] + "...")
    except Exception as e:
        return render_template('analysis.html', title='Analysis', error=str(e))

@app.route('/dashboard')
@login_required
def dashboard():
    analyzed_emails = AnalyzedEmail.query.filter_by(user_id=current_user.id).all()
    total = len(analyzed_emails)
    safety_level = (len([e for e in analyzed_emails if e.result == 'SAFE']) / total * 100) if total > 0 else 100
    return render_template('dashboard.html', title='Dashboard', analyzed_emails=analyzed_emails, safety_level=safety_level)

@app.route('/manual_analysis', methods=['GET', 'POST'])
@login_required
def manual_analysis():
    if request.method == 'POST':
        email_content = request.form['content']
        result, confidence, features, reasoning, risk_factors, safety_score = analyze_email(email_content)
        import uuid
        manual_email_id = f"manual_{uuid.uuid4()}"
        email = AnalyzedEmail(
            email_id=manual_email_id, user_id=current_user.id, sender="Manual Analysis", 
            subject="Manual Email Analysis", result=result, score=confidence, content=email_content,
            reasoning=reasoning, risk_factors=json.dumps(risk_factors), safety_score=json.dumps(safety_score)
        )
        db.session.add(email)
        db.session.commit()
        return render_template('analysis.html', title='Manual Analysis', 
                             result=result, confidence=confidence, 
                             reasoning=smart_format_reasoning(reasoning), 
                             risk_factors=risk_factors, safety_score=safety_score, content=email_content[:500] + "...")
    return render_template('manual_analysis.html', title='Manual Analysis')
