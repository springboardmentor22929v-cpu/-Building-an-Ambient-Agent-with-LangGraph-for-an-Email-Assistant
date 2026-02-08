import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Read API key
api_key = os.getenv("GOOGLE_API_KEY")

# Create Gemini client
client = genai.Client(api_key=api_key)

def triage_email(email_text: str) -> str:
    """
    Classify an email into:
    - ignore
    - notify_human
    - respond_act
    """

    prompt = f"""
You are an email assistant.

Classify the following email into ONE of these categories:
- ignore (spam, ads, newsletters)
- notify_human (important but needs human attention)
- respond_act (needs a reply or action)

Email:
\"\"\"{email_text}\"\"\"

Respond with ONLY one word:
ignore OR notify_human OR respond_act
"""

    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )

    return response.text.strip().lower()


def generate_email_draft(email_text: str) -> dict:
    """
    Generate a subject and body for the response using LLM.
    """
    prompt = f"""
    You are an helpful assistant replying to an email.
    
    Incoming Email:
    \"\"\"{email_text}\"\"\"
    
    1. Extract a clear Subject (format: Re: <Original Subject>).
    2. Write a professional, polite Body.
    
    Respond in JSON format:
    {{
        "subject": "...",
        "body": "..."
    }}
    """
    
    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )
    
    try:
        import json
        text = response.text.strip()
        # Handle markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:-3]
        return json.loads(text)
    except:
        return {
            "subject": "Re: Inquiry",
            "body": response.text
        }