# Phishing Detector

An AI-powered email phishing detection system that monitors your Gmail inbox in real-time and alerts you to potential phishing threats.

## Features

- **Real-time Gmail Integration**: Automatically monitors your inbox for new emails
- **AI-Powered Analysis**: Uses Google's Gemini AI to analyze emails for phishing indicators
- **Comprehensive Dashboard**: View analyzed emails with detailed safety scores and risk factors
- **Audio Alerts**: Plays an alert sound when a phishing email is detected
- **Web Interface**: User-friendly interface for viewing and analyzing emails

## How It Works

1. The system connects to your Gmail account using OAuth2 authentication
2. It continuously monitors your inbox for new emails
3. Each new email is automatically analyzed by Google's Gemini AI
4. The AI provides a detailed analysis including:
   - Classification (SAFE or PHISHING)
   - Confidence score
   - Detailed reasoning
   - Risk factors with severity levels
   - Safety scores
5. If a phishing email is detected, an audio alert is played
6. All analyzed emails are stored in a local database for review

## Setup

1. Clone the repository
2. Install the required dependencies: `pip install -r requirements.txt`
3. Set up a Google Cloud project with the Gemini API enabled
4. Configure OAuth2 credentials for Gmail API access
5. Add your Gemini API key to the configuration
6. Run the application: `python run.py`

## Requirements

- Python 3.7+
- Google Cloud account with Gemini API access
- Gmail account for monitoring

## Security

This application uses OAuth2 for secure Gmail access and only requests read and modify permissions for the inbox. All API keys and credentials are stored locally and are not transmitted to any external servers.