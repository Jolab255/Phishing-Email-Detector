import requests
import re
import json
import os
import time

# Gemini API configuration - using the correct model name
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def analyze_email(text):
    """Analyzes the email text for phishing using Gemini AI API."""
    print(f"Analyzing email text (length: {len(text)} characters)")
    
    # Extract key features that are often used in phishing detection
    features = extract_phishing_features(text)
    
    # Truncate text to a reasonable length for API processing
    if len(text) > 4000:
        text = text[:4000]
        print(f"Text truncated to {len(text)} characters")
    
    try:
        # Get the API key from the Flask app config
        from app import app
        api_key = app.config.get('GEMINI_API_KEY')
        print(f"API Key: {api_key}")
        print(f"API Key properly configured: {bool(api_key and api_key != 'YOUR_ACTUAL_API_KEY_HERE')}")
        
        # Use Gemini AI API for analysis if API key is available
        if api_key and api_key != 'YOUR_ACTUAL_API_KEY_HERE':
            print(f"Using Gemini AI for analysis...")
            result = analyze_with_gemini(text, api_key)
            print(f"Gemini analysis result: {result}")
            if result:
                label = result['label']
                confidence = result['confidence']
                reasoning = result.get('reasoning', 'No reasoning provided')
                
                # Extract additional information from the result
                risk_factors = result.get('risk_factors', [])
                # Ensure risk_factors is always a list with at least one item
                if not isinstance(risk_factors, list) or len(risk_factors) == 0:
                    risk_factors = [{
                        'factor': 'No significant risk factors identified',
                        'severity': 'LOW',
                        'evidence': 'N/A'
                    }]
                
                safety_score = result.get('safety_score', {
                    'overall': 0.0,
                    'urgency': 0.0,
                    'link_safety': 0.0,
                    'sender_authenticity': 0.0,
                    'content_trustworthiness': 0.0
                })
                
                print(f"Gemini AI analysis result: {label} (confidence: {confidence})")
                print(f"Reasoning: {reasoning}")
                return label, confidence, features, reasoning, risk_factors, safety_score
            else:
                print("Gemini AI analysis failed...")
                # Return error indication when AI analysis fails
                error_reasoning = "AI analysis failed. Please try again later."
                return "ERROR", 0.0, features, error_reasoning, [], {
                    'overall': 0.0,
                    'urgency': 0.0,
                    'link_safety': 0.0,
                    'sender_authenticity': 0.0,
                    'content_trustworthiness': 0.0
                }
        else:
            print("Gemini API key not properly configured...")
            if not api_key:
                print("API key is None or empty")
            elif api_key == 'YOUR_ACTUAL_API_KEY_HERE':
                print("API key is still the placeholder value")
            
            # Return error indication when API key is not configured
            error_reasoning = "AI service not properly configured. Please check API key settings."
            return "ERROR", 0.0, features, error_reasoning, [], {
                'overall': 0.0,
                'urgency': 0.0,
                'link_safety': 0.0,
                'sender_authenticity': 0.0,
                'content_trustworthiness': 0.0
            }
            
    except Exception as e:
        print(f"Error in email analysis: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error indication when there's an exception
        error_reasoning = f"Error during AI analysis: {str(e)}"
        return "ERROR", 0.0, features, error_reasoning, [], {
            'overall': 0.0,
            'urgency': 0.0,
            'link_safety': 0.0,
            'sender_authenticity': 0.0,
            'content_trustworthiness': 0.0
        }

def analyze_with_gemini(text, api_key):
    """Analyze text using Gemini AI API with retry logic."""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            prompt = f"""
            Analyze email for phishing. Respond ONLY with JSON (no markdown). ALWAYS include at least one risk factor in the risk_factors array, even if it's just "No significant risk factors identified" with LOW severity.
            {{
                "label": "PHISHING" or "SAFE",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation",
                "risk_factors": [
                    {{
                        "factor": "description of risk factor or 'No significant risk factors identified'",
                        "severity": "LOW", 
                        "evidence": "specific words or phrases or 'N/A'"
                    }}
                ],
                "safety_score": {{
                    "overall": 0.0-100.0,
                    "urgency": 0.0-100.0,
                    "link_safety": 0.0-100.0,
                    "sender_authenticity": 0.0-100.0,
                    "content_trustworthiness": 0.0-100.0
                }}
            }}
            Email:
            {text}
            """
            
            print("Sending request to Gemini AI...")
            print(f"Text length: {len(text)} characters")
            print(f"Attempt {attempt + 1}/{max_retries}")
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json"
                }
            }
            
            response = requests.post(
                f"{GEMINI_API_URL}?key={api_key}",
                headers=headers,
                json=data,
                timeout=60  # Increased timeout to 60 seconds
            )
            
            print(f"Gemini API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Raw Gemini response: {json.dumps(result, indent=2)}")
                
                gemini_response_text = extract_gemini_text(result)
                print(f"Gemini response content: {gemini_response_text}")

                # Improved cleaning logic to handle various Markdown formats
                if gemini_response_text:
                    # Remove leading/trailing whitespace and newlines
                    clean_text = gemini_response_text.strip()
                    
                    # Remove Markdown code block markers
                    if clean_text.startswith("```"):
                        # Find the end of the opening marker
                        first_newline = clean_text.find('\n')
                        if first_newline != -1:
                            # Remove the opening marker and language identifier
                            clean_text = clean_text[first_newline + 1:]
                    
                    # Remove closing marker if present
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    
                    # Additional cleaning
                    clean_text = clean_text.strip()
                    
                    # Try to parse as JSON
                    try:
                        analysis = json.loads(clean_text)
                        
                        # Ensure risk_factors is always present and is a list
                        if 'risk_factors' not in analysis or not isinstance(analysis['risk_factors'], list):
                            analysis['risk_factors'] = [
                                {
                                    'factor': 'No significant risk factors identified',
                                    'severity': 'LOW',
                                    'evidence': 'N/A'
                                }
                            ]
                        elif len(analysis['risk_factors']) == 0:
                            analysis['risk_factors'] = [
                                {
                                    'factor': 'No significant risk factors identified',
                                    'severity': 'LOW',
                                    'evidence': 'N/A'
                                }
                            ]
                        
                        return analysis
                    except json.JSONDecodeError as e:
                        print("⚠️ Could not parse Gemini response. JSON decode error:", str(e))
                        print("Raw content:", gemini_response_text)
                        print("Cleaned content:", clean_text)
                        return None
                else:
                    print("⚠️ Empty Gemini response received.")
                    return None
            else:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    return None
                    
        except requests.exceptions.Timeout:
            print(f"Gemini API timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            else:
                print("Max retries exceeded. API timeout.")
                return None
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            else:
                return None
    
    return None

def extract_gemini_text(response_json):
    try:
        candidates = response_json.get("candidates", [])
        if not candidates:
            print("⚠️ No candidates returned.")
            return None

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if not parts:
            print(f"⚠️ No content parts returned. Raw content: {content}")
            return None

        analysis_text = parts[0].get("text", "").strip()
        if not analysis_text:
            print(f"⚠️ Gemini returned empty text. Raw content: {content}")
            return None

        return analysis_text
    except Exception as e:
        print(f"Gemini analysis error: {e}")
        return None



def extract_phishing_features(text):
    """Extract common phishing features from email text."""
    features = {
        'urgent_language': 0,
        'suspicious_links': 0,
        'grammar_errors': 0,
        'suspicious_sender': 0,
        'requests_sensitive_info': 0
    }
    
    # Check for urgent language
    urgent_patterns = ['urgent', 'immediate', 'act now', 'limited time', 'asap', 'hurry', 'quick action']
    for pattern in urgent_patterns:
        if pattern in text.lower():
            features['urgent_language'] += 1
    
    # Check for suspicious links
    link_patterns = [r'http://[^s]', r'https?://[^\s]*\.[^\s]{5,}']
    for pattern in link_patterns:
        if re.search(pattern, text):
            features['suspicious_links'] += 1
    
    # Check for requests for sensitive information
    sensitive_patterns = ['password', 'credit card', 'social security', 'account number', 'pin', 'cvv']
    for pattern in sensitive_patterns:
        if pattern in text.lower():
            features['requests_sensitive_info'] += 1
    
    # Simple grammar error detection (basic)
    # Check for excessive exclamation marks
    if text.count('!') > 3:
        features['grammar_errors'] += 1
    
    return features