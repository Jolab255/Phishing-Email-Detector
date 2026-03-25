import os

class Config:
    # Use environment variables or default values
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this-in-prod'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # GEMINI AI API Key - Get yours from https://aistudio.google.com/
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'YOUR_API_KEY_HERE'
