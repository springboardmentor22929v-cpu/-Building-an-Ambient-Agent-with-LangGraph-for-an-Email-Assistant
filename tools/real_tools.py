# tools/real_tools.py
import os
import datetime
import base64
from email.mime.text import MIMEText
from langchain_core.tools import tool

# Google Library Imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ==========================================
# 1. SETUP PERMISSIONS
# ==========================================
# We added 'calendar.readonly' to the list so we can check your schedule.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly'
]

def get_google_creds():
    """
    Handles the login for BOTH Gmail and Calendar.
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.path.exists('credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            else:
                print("❌ ERROR: 'credentials.json' missing.")
                return None
    return creds

# ==========================================
# 2. REAL GMAIL TOOL
# ==========================================
@tool
def write_email(to: str, subject: str, content: str) -> str:
    """
    Sends an ACTUAL email using the Gmail API. 
    """
    creds = get_google_creds()
    if not creds: return "Authentication Failed."
    
    service = build('gmail', 'v1', credentials=creds)

    try:
        message = MIMEText(content)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        
        sent = service.users().messages().send(userId="me", body=body).execute()
        return f"✅ Email SENT! ID: {sent['id']}"
    except Exception as e:
        return f"❌ Failed to send email: {e}"

# ==========================================
# 3. REAL CALENDAR TOOL (New!)
# ==========================================
@tool
def check_calendar(date_str: str = None) -> str:
    """
    Checks the user's REAL Google Calendar for upcoming events.
    args:
        date_str: Optional date description (e.g., '2025-01-25'). 
                  If empty, defaults to the next 7 days.
    """
    creds = get_google_creds()
    if not creds: return "Authentication Failed."
    
    service = build('calendar', 'v3', credentials=creds)

    try:
        # Get current time in UTC (Google requires this format)
        now = datetime.datetime.utcnow().isoformat() + 'Z' 
        
        # Ask Google for the next 5 events
        print(f"📅 [SYSTEM] Checking Real Calendar...")
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now,
            maxResults=5, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return "📅 Calendar Status: You have NO upcoming events found."
        
        # Format the list of events nicely
        event_list = "📅 Upcoming Events:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            event_list += f"- {start}: {summary}\n"
            
        return event_list

    except Exception as e:
        return f"❌ Failed to check calendar: {e}"