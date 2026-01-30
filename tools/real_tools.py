# tools/real_tools.py
import os
import datetime
import json  # <-- NEW: Required for structured data output
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_core.tools import tool

# PERMISSIONS
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_google_creds():
    """
    Shared Authentication Helper.
    Used by both real_tools.py and fetch_tool.py
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Sends an ACTUAL email using Gmail API."""
    creds = get_google_creds()
    if not creds: return '{"error": "Authentication Failed"}'
    
    service = build('gmail', 'v1', credentials=creds)

    try:
        message = MIMEText(content)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        
        sent = service.users().messages().send(userId="me", body=body).execute()
        
        # --- RETURN JSON ---
        # We return a JSON string so the AI knows exactly what happened.
        return json.dumps({
            "status": "success", 
            "message_id": sent['id'], 
            "action": "email_sent"
        })

    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def check_calendar(date_str: str = None) -> str:
    """
    Checks the user's REAL Google Calendar.
    RETURNS: A JSON string of events (or an empty list if free).
    """
    creds = get_google_creds()
    if not creds: return '{"error": "Authentication Failed"}'
    
    service = build('calendar', 'v3', credentials=creds)

    try:
        # 1. Setup Time Range (Check from NOW)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print(f"📅 [SYSTEM] Checking Real Calendar...")
        
        # 2. Call Google API
        events_result = service.events().list(
            calendarId='primary', timeMin=now, maxResults=10, 
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        raw_events = events_result.get('items', [])
        
        # --- THE FIX: CLEAN DATA LIST ---
        # Instead of building a text sentence ("You have a meeting..."),
        # we build a structured list of data objects.
        clean_events = []

        if not raw_events:
            # If empty, return a clear "Empty" JSON signal.
            # The AI sees 'events': [] and knows "I AM FREE".
            return json.dumps({
                "events": [], 
                "message": "No upcoming events found. User is free."
            })
        
        # Loop through raw events and pick only what we need
        for event in raw_events:
            # Extract Start Time (Google hides it in 'dateTime' or 'date')
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Extract Title
            summary = event.get('summary', 'No Title')
            
            # Add to our clean list
            clean_events.append({
                "start": start,
                "summary": summary
            })
            
        # 3. Return the List as JSON
        # The AI receives: {"events": [{"start": "2026-02-01...", "summary": "Meeting"}]}
        return json.dumps({"events": clean_events})

    except Exception as e:
        return json.dumps({"error": str(e)})