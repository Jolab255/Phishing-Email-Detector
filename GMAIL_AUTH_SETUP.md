# Gmail OAuth Authentication Setup Guide

This guide explains how to properly set up Gmail OAuth authentication for testing the phishing detector application.

## Prerequisites

1. A Google account
2. Access to Google Cloud Console
3. Basic understanding of OAuth 2.0

## Setting Up OAuth Credentials

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project

### Step 2: Configure OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (for testing purposes)
3. Fill in the required application information:
   - App name: Phishing Detector Test
   - User support email: Your email
   - Developer contact information: Your email
4. Add the following scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.modify`
5. Add your email as a test user under "Test users" section

### Step 3: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop application" as the application type
4. Download the JSON file and save it as `credentials.json` in the project root directory

### Step 4: Run Authentication

1. Delete any existing `token.json` file:
   ```bash
   rm token.json
   ```
2. Run the application or test script:
   ```bash
   python test_gmail_auth.py
   ```
3. Follow the OAuth consent flow in your browser
4. Grant the requested permissions

## Testing with Different Email Accounts

During development, you can test with different email accounts by:

1. Deleting the `token.json` file
2. Running the authentication flow again
3. Signing in with a different Google account

## Troubleshooting

### Common Issues

1. **"Access blocked: Authorization Error"**
   - Solution: Ensure your email is added as a test user in the Google Cloud Console

2. **Invalid credentials.json file**
   - Solution: Recreate the OAuth client ID and download a fresh credentials.json

3. **Token refresh failures**
   - Solution: Re-authenticate by deleting token.json and running the auth flow again

### Development vs Production

For production deployment:
1. Change the OAuth consent screen to "Internal" or publish it for public use
2. Go through Google's verification process
3. Use a web application OAuth flow instead of desktop application flow

## Security Considerations

1. Never commit `credentials.json` or `token.json` to version control
2. The `.gitignore` file should exclude these files
3. Store credentials securely in production environments
4. Regularly rotate OAuth credentials

## Running Tests

After setting up authentication, you can run the Gmail tests:

```bash
python test_gmail.py
python test_gmail_auth.py
```

These tests will verify that:
1. Authentication is working correctly
2. The Gmail API is accessible
3. Tokens can be refreshed when expired