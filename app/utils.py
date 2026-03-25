import re

def smart_format_reasoning(raw_text):
    """
    Cleans and formats Gemini AI reasoning text into well-structured HTML.
    Works with paragraphs, numbered lists, or mixed AI outputs.
    """

    if not raw_text:
        return "<p><i>No reasoning provided.</i></p>"

    # 1. Clean unwanted Markdown/backticks
    text = re.sub(r"^```[a-zA-Z]*|```$", "", raw_text.strip())

    # 2. Normalize spaces
    text = re.sub(r"\s+", " ", text)

    # 3. Add line breaks between sentences (split on . ! or ? followed by a space + capital)
    text = re.sub(r"(?<=[.!?])\s+(?=[A-Z])", "<br><br>", text)

    # 4. Highlight strong indicators (words often used in reasoning)
    keywords = [
        "legitimate", "phishing", "suspicious", "malicious", "safe",
        "warning", "urgent", "secure", "trusted", "fake",
        "domain", "URL", "attachment", "sender", "link",
        "confidence", "reasoning", "analysis", "indicators"
    ]
    for word in keywords:
        text = re.sub(fr"\b({word})\b", r"<b>\1</b>", text, flags=re.IGNORECASE)

    # 5. Wrap for clean display
    return f"<div class='reasoning-content'>{text}</div>"