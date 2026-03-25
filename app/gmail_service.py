import os.path
import json
from flask import url_for, request
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service(user_id=None):
    """Gets the Gmail service for a user. returns None if not authenticated."""
    if user_id is None:
        from flask_login import current_user
        user_id = current_user.id

    token_path = f'tokens/token_{user_id}.json'
    if not os.path.exists(token_path):
        return None

    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        print(f"Error getting service: {e}")
        return None

def get_auth_flow(redirect_uri):
    """Creates a flow object for the Web OAuth process."""
    return Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
