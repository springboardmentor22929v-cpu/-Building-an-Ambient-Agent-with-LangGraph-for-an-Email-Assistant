import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini with API key from .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Gemini 2.5 Flash model
MODEL = "gemini-2.5-flash"


def triage_email(email_text: str) -> str:
    prompt = f"""
    Classify this email into ONE category:
    - ignore
    - notify_human
    - respond/act

    Email:
    {email_text}

    Return only one word.
    """

    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)

    result = response.text.strip().lower()

    if "ignore" in result:
        return "ignore"
    if "notify" in result:
        return "notify_human"
    return "respond/act"
