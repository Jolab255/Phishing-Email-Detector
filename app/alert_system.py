try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not found. Audio alerts will be disabled.")
import os
from datetime import datetime

def play_alert_sound():
    """Plays an alert sound."""
    if not PYGAME_AVAILABLE:
        print("Audio alert skipped (pygame not installed)")
        return

    try:
        # Check if the alert file exists
        if not os.path.exists("app/static/alert.wav"):
            print("Alert sound file not found!")
            return
            
        pygame.mixer.init()
        pygame.mixer.music.load("app/static/alert.wav")
        pygame.mixer.music.play()
        print("Alert sound played successfully!")
        
        # Wait for the sound to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Error playing alert sound: {e}")

def show_desktop_notification(title, message):
    """Show desktop notification (cross-platform)"""
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Simple console alert for Windows
            print(f"🔔 DESKTOP ALERT: {title} - {message}")
                
        elif system == "Darwin":  # macOS
            # macOS notification
            os.system(f"osascript -e 'display notification \"{message}\" with title \"{title}\"'")
            
        else:  # Linux
            # Linux notification
            try:
                os.system(f'notify-send "{title}" "{message}"')
            except:
                print(f"🔔 DESKTOP ALERT: {title} - {message}")
                
    except Exception as e:
        print(f"Error showing desktop notification: {e}")
        # Fallback to console
        print(f"🔔 DESKTOP ALERT: {title} - {message}")

def trigger_phishing_alert(email_data, analysis_result):
    """Trigger all automatic alert mechanisms"""
    subject = email_data.get('subject', 'No Subject')
    sender = email_data.get('sender', 'Unknown Sender')
    
    # Audio alert
    play_alert_sound()
    
    # Desktop notification
    show_desktop_notification(
        "Phishing Alert Detected!", 
        f"Potential phishing from {sender}\nSubject: {subject}"
    )
    
    # Console alert
    print("=" * 60)
    print("🚨 PHISHING ALERT DETECTED! 🚨")
    print(f"From: {sender}")
    print(f"Subject: {subject}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Confidence: {analysis_result.get('confidence', 0.0)*100:.1f}%")
    print("=" * 60)
    
    return True
