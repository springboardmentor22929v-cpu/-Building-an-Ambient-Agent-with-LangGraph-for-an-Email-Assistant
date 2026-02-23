# m4_tools.py
import os
import datetime
import base64
from email.message import EmailMessage
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Expanded scopes for M4
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_service(service_name: str, version: str = 'v3'):
    """Authenticate and return a Google API service."""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            print("⚠️ Token file invalid or scopes changed.")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                print("⚠️ Refresh failed, re-authenticating.")
                creds = None
        
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(f"❌ '{CREDENTIALS_FILE}' not found. Please download it from Google Cloud Console.")
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build(service_name, version, credentials=creds)

# ==================================================
# 🗓️ Calendar Tools (Real)
# ==================================================

def check_calendar_availability(date_str: str, time_str: str = None) -> str:
    """
    Check calendar for events on a specific date (and optional time).
    Accepts date in ISO format (YYYY-MM-DD) or flexible strings if parsed.
    For this implementation, we assume ISO or simple parsing.
    """
    print(f"🗓️ Checking real calendar for {date_str}...")
    try:
        service = get_service('calendar', 'v3')
        
        # Parse date (basic handling)
        # Ideally, use an LLM or library to parse "Next Friday" to "2024-..."
        # Here we expect the LLM to provide YYYY-MM-DD
        try:
           dt_start = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"❌ Date format error. Please use YYYY-MM-DD format (e.g., 2024-12-25)."

        # Range: Full day
        time_min = dt_start.isoformat() + 'Z'
        time_max = (dt_start + datetime.timedelta(days=1)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary', timeMin=time_min, timeMax=time_max,
            singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return f"✅ No events found on {date_str}. You are free."

        summary = f"📅 Events on {date_str}:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary += f"- {start}: {event['summary']}\n"
            
        return summary
        
    except Exception as e:
        return f"❌ Error checking calendar: {e}"

def schedule_meeting(summary: str, start_time: str, duration_mins: int = 60) -> str:
    """
    Schedule a meeting on Google Calendar.
    start_time: ISO format string (e.g., 2024-12-25T15:00:00)
    """
    print(f"📅 Scheduling '{summary}' at {start_time}...")
    try:
        service = get_service('calendar', 'v3')
        
        start_dt = datetime.datetime.fromisoformat(start_time)
        end_dt = start_dt + datetime.timedelta(minutes=duration_mins)
        
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC', # Adjust if local timezone needed
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Meeting scheduled! Link: {event.get('htmlLink')}"
        
    except Exception as e:
        return f"❌ Error scheduling meeting: {e}"

# ==================================================
# 📧 Gmail Tools (Real Wrapper)
# ==================================================

def draft_email_reply(subject: str, body: str, to: str = "") -> str:
    """Create a draft in Gmail."""
    print("✉️ Creating real draft...")
    try:
        service = get_service('gmail', 'v1')
        
        message = EmailMessage()
        message.set_content(body)
        if to:
            message['To'] = to
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message}}
        
        draft = service.users().drafts().create(userId="me", body=create_message).execute()
        return f"✅ Draft created! ID: {draft['id']}"
    except Exception as e:
        return f"❌ Error creating draft: {e}"

def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using Gmail API."""
    print(f"🚀 Sending real email to {to}...")
    try:
        service = get_service('gmail', 'v1')
        
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        # Correct flat structure fixed in M3
        create_message = {'raw': encoded_message}
        
        sent_message = service.users().messages().send(userId="me", body=create_message).execute()
        return f"✅ Email SENT! ID: {sent_message['id']}"
    except Exception as e:
        return f"❌ Failed to send email: {e}"

# 🚨 Dangerous Tools Registry for M4
DANGEROUS_TOOLS = {
    "schedule_meeting",
    "send_email"
}
