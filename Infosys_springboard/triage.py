import os
import time
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Read API key
api_key = os.getenv("GOOGLE_API_KEY")

# Create Gemini client
client = genai.Client(api_key=api_key)

MODEL = "models/gemini-2.5-flash"

def call_gemini(prompt, max_retries=3):
    """Call Gemini with automatic retry on rate limit (429) errors."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            return response
        except Exception as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait = 15 * (attempt + 1)
                print(f"⏳ Rate limited, waiting {wait}s before retry ({attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise

def triage_email(email_text: str) -> str:
    """
    Classify an email into:
    - ignore
    - notify_human
    - respond_act
    """

    prompt = f"""
You are an email triage assistant. Classify the email into EXACTLY ONE category:

- ignore: spam, promotions, newsletters, ads, automated notifications with no action needed
  Examples: "You have a new follower", "50% off sale today!", newsletter digests

- notify_human: announcements and informational emails where the sender is TELLING you something.
  No reply is needed — the user just needs to be aware.
  Examples: invoice/payment notices, security alerts, policy updates, HR announcements,
  system notifications, "your account has been updated", overdue payment notices.
  KEY SIGNAL: emails starting with "Please be informed", "We are pleased to inform",
  "This is to notify", "Please note", "FYI", company-wide announcements.

- respond_act: emails where the sender is DIRECTLY ASKING you a question or requesting something.
  A reply or specific action from you is expected.
  Examples: "Can you review my PR?", "Are you free for a meeting?", 
  "Can you send me the report?", "I need your feedback on..."

Email:
\"\"\"{email_text}\"\"\"

RULES:
1. If the email is an announcement or policy update → notify_human (even if it says "acknowledge")
2. If someone is asking YOU a direct question → respond_act
3. If it is promotional or auto-generated with no relevance → ignore

Respond with ONLY one word: ignore OR notify_human OR respond_act
"""

    response = call_gemini(prompt)

    return response.text.strip().lower()


def generate_email_draft(email_text: str, preferences: dict = None) -> dict:
    """
    Generate a subject and body for the response using LLM.
    Accepts specific user preferences (e.g. tone, sign-off).
    """
    
    pref_instruction = ""
    if preferences:
        pref_instruction = "\n\nUser Preferences (MANDATORY - YOU MUST APPLY THESE EXACTLY):\n"
        for k, v in preferences.items():
            pref_instruction += f"- {k}: {v}\n"
        pref_instruction += "\nCRITICAL RULES:\n"
        pref_instruction += "- NEVER use placeholder text like [Your Name], [Name], or [Recipient]. Use real names from the email context.\n"
        pref_instruction += "- If the sender's name is in the email, use it in the greeting.\n"
        pref_instruction += "- Sign off with 'Abinaya' as the sender name (the user's name).\n"
    
    prompt = f"""
    You are a helpful assistant replying to an email on behalf of the user.
    {pref_instruction}
    
    Incoming Email:
    \"\"\"{email_text}\"\"\"
    
    Instructions:
    1. Extract a clear Subject (format: Re: <Original Subject>).
    2. Write a professional, polite Body.
    
    Respond in JSON format:
    {{
        "subject": "...",
        "body": "..."
    }}
    """
    
    response = call_gemini(prompt)
    
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