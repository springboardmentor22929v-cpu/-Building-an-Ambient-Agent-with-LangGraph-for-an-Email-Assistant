# tools.py

from langchain_core.tools import tool
from typing import List
from pydantic import BaseModel,Field
from google_auth import get_credentials
from email.mime.text import MIMEText
import base64
from googleapiclient.discovery import build
from email.message import EmailMessage

@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Sends an email. Note: 'to' must be a valid email address."""
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)

        # Use EmailMessage for better RFC 5322 compliance
        message = EmailMessage()
        message.set_content(content)
        message["To"] = to
        message["From"] = "me" # "me" tells Gmail to use your primary email
        message["Subject"] = subject

        # CRITICAL: Google requires base64URL encoding
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message = {"raw": encoded_message}
        
        # Execute the send
        sent_message = service.users().messages().send(
            userId="me", 
            body=create_message
        ).execute()

        print(f"Direct Send Success! ID: {sent_message['id']}")
        return f"Email sent successfully to {to}."
    except Exception as e:
        print(f"Error in write_email tool: {e}")
        return f"Failed to send: {e}"


@tool
def check_calendar_availability(
    start_time: str,
    end_time: str
) -> str:
    """Check if the user is available in the given time window.
    Input times should be in ISO format or YYYY-MM-DD HH:MM:SS format.
    """
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        # --- FIX: Format the strings for Google API ---
        def format_for_google(dt_str):
            dt_str = dt_str.strip()
            # Replace space with 'T' if the LLM sent a space
            if " " in dt_str:
                dt_str = dt_str.replace(" ", "T")
            # Add 'Z' (UTC) if no timezone offset is present
            if not dt_str.endswith('Z') and '+' not in dt_str and '-' not in dt_str[10:]:
                dt_str += 'Z'
            return dt_str

        google_start = format_for_google(start_time)
        google_end = format_for_google(end_time)
        # ----------------------------------------------

        events = service.events().list(
            calendarId="primary",
            timeMin=google_start,
            timeMax=google_end,
            singleEvents=True
        ).execute()

        if events.get("items"):
            return "The time slot is not available."
        else:
            return "The time slot is available."

    except Exception as e:
        # This will now catch and report if the string is still un-parseable
        return f"Failed to check availability: {str(e)}"


@tool
def schedule_meeting(
    title: str,
    start_time: str,
    end_time: str,
    attendees: list[str] = []
) -> str:
    """Schedule a meeting on the calendar. 
    Times should be in YYYY-MM-DD HH:MM:SS format.
    """

    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        # Helper function to fix format (Space -> T)
        def format_dt(dt_str):
            dt_str = dt_str.strip()
            if " " in dt_str:
                dt_str = dt_str.replace(" ", "T")
            return dt_str

        event = {
            "summary": title,
            "start": {
                "dateTime": format_dt(start_time), 
                "timeZone": "Asia/Kolkata"
            },
            "end": {
                "dateTime": format_dt(end_time), 
                "timeZone": "Asia/Kolkata"
            },
            "attendees": [{"email": a} for a in attendees],
        }

        created = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()

        return f"Meeting scheduled successfully. Event ID: {created['id']}"

    except Exception as e:
        # This will catch if the time format is still wrong or if there's a 400 error
        return f"Failed to schedule meeting: {str(e)}"

@tool
def Done() -> str:
    """
    Signal that the task is complete.
    """
    return "Task completed."

@tool
class Question(BaseModel):
      """
    Use this tool to ask the human user a question when you need more information 
    to complete a task (like missing email addresses or meeting times). 
    This tool will pause the agent and wait for the user's response.
    """
      content: str = Field(description="The question text you want to show to the user.")
