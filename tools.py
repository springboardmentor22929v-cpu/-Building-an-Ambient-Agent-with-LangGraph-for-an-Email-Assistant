import os
import base64
from typing import Dict, Any, List
from datetime import datetime
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar"
]

def get_google_credentials():
    """Gets valid user credentials from storage or initiates OAuth2 flow."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("credentials.json not found. Please add it to the project root.")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    return creds

def create_message(to: str, subject: str, content: str) -> Dict[str, str]:
    """Creates a MIME message for Gmail API."""
    message = MIMEText(content)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}

def write_email(to: str, subject: str, content: str) -> str:
    """Sends an email using Gmail API."""
    try:
        creds = get_google_credentials()
        service = build("gmail", "v1", credentials=creds)
        message = create_message(to, subject, content)
        
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=message)
            .execute()
        )
        return f"Email sent to {to}. Message Id: {send_message['id']}"
    except Exception as e:
        return f"Error sending email: {str(e)}"

def check_calendar_availability(date_str: str) -> str:
    """
    Checks calendar availability for a given date.
    Args:
        date_str: Date string in 'YYYY-MM-DD' format.
    """
    try:
        creds = get_google_credentials()
        service = build("calendar", "v3", credentials=creds)
        
        # Parse date and set time range for the full day
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        time_min = target_date.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        time_max = target_date.replace(hour=23, minute=59, second=59).isoformat() + "Z"
        
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min, 
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return f"No events found on {date_str}. The day is completely free."
        
        availability_summary = f"Busy slots on {date_str}:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'Busy')
            availability_summary += f"- {start} to {end}: {summary}\n"
            
        return availability_summary
        
    except Exception as e:
        return f"Error checking calendar: {str(e)}"

def schedule_meeting(
    attendees: List[str], 
    subject: str, 
    start_time: str, 
    duration_minutes: int = 60
) -> str:
    """
    Schedules a meeting on Google Calendar.
    Args:
        attendees: List of email addresses.
        subject: Meeting title.
        start_time: Start time in ISO format (e.g., '2024-01-22T15:00:00').
        duration_minutes: Duration in minutes.
    """
    try:
        creds = get_google_credentials()
        service = build("calendar", "v3", credentials=creds)
        
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromtimestamp(start_dt.timestamp() + duration_minutes * 60)
        
        event = {
            'summary': subject,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC', # Adjust/detect as needed or strictly use ISO with offsets
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [{'email': email} for email in attendees],
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Meeting scheduled: {event.get('htmlLink')}"
        
    except Exception as e:
        return f"Error scheduling meeting: {str(e)}"

# Alias implementation for fallback compatibility if needed
read_calendar = check_calendar_availability
