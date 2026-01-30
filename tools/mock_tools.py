# tools/mock_tools.py
import json
from langchain_core.tools import tool

@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Simulates sending an email."""
    print(f"\n📧 [MOCK] Sending Email to {to}")
    print(f"   Subject: {subject}")
    print(f"   Content: {content[:50]}...")
    
    # Return JSON to match Real Tool behavior
    return json.dumps({
        "status": "success", 
        "action": "email_sent",
        "recipient": to
    })

@tool
def check_calendar(date_str: str = None) -> str:
    """
    Simulates checking the calendar.
    Returns JSON data just like the Real Tool.
    """
    print(f"\n📅 [MOCK] Checking Calendar for {date_str}...")
    
    # SCENARIO 1: If user asks for "tomorrow at 2pm", let's pretend we are BUSY.
    # (You can change this logic to test different scenarios)
    if "2026-02-01" in str(date_str): 
        events = [
            {
                "start": "2026-02-01T14:00:00", 
                "summary": "Existing Client Meeting"
            }
        ]
        return json.dumps({"events": events})

    # SCENARIO 2: Default to FREE (Empty List)
    return json.dumps({
        "events": [],
        "message": "No events found. User is free."
    })

@tool
def fetch_unread_emails() -> str:
    """Simulates fetching unread emails."""
    # This tool is usually hidden from the agent in 'tool_loader.py', 
    # but we keep it here for manual testing if needed.
    emails = [
        {
            "sender": "boss@company.com", 
            "subject": "Urgent Meeting", 
            "body": "Can we meet tomorrow at 2pm?"
        }
    ]
    return json.dumps({"emails": emails})