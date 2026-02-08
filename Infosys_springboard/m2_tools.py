# tools.py
"""
Milestone 2 – Tool functions for Email Agent
These simulate real-world actions.
"""

import base64
from datetime import datetime
from email.message import EmailMessage
from gmail_reader import get_gmail_service, send_gmail_message


# ==================================================
# 🚨 Milestone 3: Dangerous tool registry
# ==================================================
DANGEROUS_TOOLS = {
    "schedule_meeting",
    "send_email"
}


# --------------------------------------------------
# TOOL 1: Check calendar availability
# --------------------------------------------------
def check_calendar_availability(date: str, time: str) -> str:
    """
    Mock function to check calendar availability.
    """
    print(f"🗓️ Checking calendar for {date} at {time}")

    # Mock logic
    if time in ["3 PM", "10 AM"]:
        return f"Available on {date} at {time}"
    else:
        return f"Not available on {date} at {time}"


# --------------------------------------------------
# TOOL 2: Schedule meeting
# --------------------------------------------------
def schedule_meeting(date: str, time: str, with_person: str) -> str:
    """
    Mock function to schedule a meeting.
    """
    print(f"📅 Scheduling meeting with {with_person} on {date} at {time}")

    return f"Meeting scheduled with {with_person} on {date} at {time}"


def draft_email_reply(subject: str, body: str) -> str:
    """
    Create a draft email in Gmail.
    """
    print("✉️ Creating draft in Gmail...")
    
    try:
        service = get_gmail_service()
        
        message = EmailMessage()
        message.set_content(body + "\n\nRegards,\nAbinaya")
        message["To"] = "" # Left blank for now, or could extract from thread
        message["Subject"] = f"Re: {subject}"
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message = {
            'message': {
                'raw': encoded_message
            }
        }
        
        draft = service.users().drafts().create(userId="me", body=create_message).execute()
        
        return f"✅ Draft created in Gmail! ID: {draft['id']}"
        
    except Exception as e:
        print(f"❌ Error creating draft: {e}")
        return f"Failed to create draft: {e}"


# --------------------------------------------------
# TOOL 4: Send email (Post-Approval)
# --------------------------------------------------
def send_email(to: str, subject: str, body: str) -> str:
    """
    Actually send an email.
    """
    print(f"🚀 Sending email to {to}...")
    try:
        result = send_gmail_message(to, subject, body)
        return f"✅ Email SENT successfully! ID: {result['id']}"
    except Exception as e:
        return f"❌ Failed to send email: {e}"
