from langchain.tools import tool
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pytz
from googleapiclient.errors import HttpError

# Global services (will be set when tools are initialized)
_gmail_service = None
_calendar_service = None


def initialize_tools(gmail_service, calendar_service):
    """
    Initialize tools with authenticated Google services.
    Call this before using any tools.
    """
    global _gmail_service, _calendar_service
    _gmail_service = gmail_service
    _calendar_service = calendar_service
    print("✅ Tools initialized with Google services")


@tool
def check_calendar(
    start_date: str,
    end_date: str,
    timezone: str = "Asia/Kolkata"
) -> str:
    """
    Check calendar for available time slots between two dates.
    
    Args:
        start_date: Start date in DD-MM-YYYY format (e.g., "15-01-2025")
        end_date: End date in DD-MM-YYYY format (e.g., "18-01-2025")
        timezone: Timezone for the check (default: Asia/Kolkata)
    
    Returns:
        String describing available time slots
    
    Example:
        check_calendar("15-01-2025", "16-01-2025")
        
    Returns something like:
        "Available slots:
        - Monday Jan 15: 10:00 AM - 11:00 AM, 2:00 PM - 3:00 PM
        - Tuesday Jan 16: 9:00 AM - 10:00 AM, 3:00 PM - 4:00 PM"
    """
    if not _calendar_service:
        return "Error: Calendar service not initialized. Call initialize_tools() first."
    
    try:
        # print(f"📅 Checking calendar from {start_date} to {end_date}")
        
        # Convert dates to RFC3339 format
        tz = pytz.timezone(timezone)
        
        # Start of first day (9 AM)
        start_datetime = datetime.strptime(start_date, "%d-%m-%Y")
        start_datetime = start_datetime.replace(hour=9, minute=0, second=0)
        start_datetime = tz.localize(start_datetime)
        
        # End of last day (5 PM)
        end_datetime = datetime.strptime(end_date, "%d-%m-%Y")
        end_datetime = end_datetime.replace(hour=17, minute=0, second=0)
        end_datetime = tz.localize(end_datetime)
        
        # Get busy times from calendar
        body = {
            "timeMin": start_datetime.isoformat(),
            "timeMax": end_datetime.isoformat(),
            "timeZone": timezone,
            "items": [{"id": "primary"}]
        }
        
        freebusy = _calendar_service.freebusy().query(body=body).execute()
        busy_times = freebusy['calendars']['primary']['busy']
        
        print(f"   Found {len(busy_times)} busy periods")
        
        # Find available slots
        available_slots = []
        current_day = start_datetime
        
        while current_day.date() <= end_datetime.date():
            # Skip weekends
            if current_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
                current_day += timedelta(days=1)
                continue
            
            # Check each hour from 9 AM to 5 PM
            day_start = current_day.replace(hour=9, minute=0)
            day_end = current_day.replace(hour=17, minute=0)
            
            day_slots = []
            current_time = day_start
            
            while current_time < day_end:
                slot_end = current_time + timedelta(hours=1)
                
                # Check if this slot conflicts with busy times
                is_free = True
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    
                    # Check for overlap
                    if not (slot_end <= busy_start or current_time >= busy_end):
                        is_free = False
                        break
                
                if is_free:
                    day_slots.append(f"{current_time.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}")
                
                current_time = slot_end
            
            if day_slots:
                day_name = current_day.strftime("%A %b %d")
                available_slots.append(f"{day_name}: {', '.join(day_slots[:3])}")  # Max 3 slots per day
            
            current_day += timedelta(days=1)
        
        if available_slots:
            result = "Available time slots:\n" + "\n".join([f"  • {slot}" for slot in available_slots])
            print(f"   ✓ Found {len(available_slots)} available days")
            return result
        else:
            return "No available time slots found in the specified date range."
    
    except HttpError as e:
        error_msg = f"Calendar API error: {e}"
        print(f"   ✗ {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error checking calendar: {str(e)}"
        print(f"   ✗ {error_msg}")
        return error_msg


@tool
def schedule_meeting(
    title: str,
    start_time: str,
    duration_minutes: int,
    attendees: str,
    description: str = "",
    timezone: str = "Asia/Kolkata"
) -> str:
    """
    Schedule a meeting on Google Calendar.
    
    Args:
        title: Meeting title/subject
        start_time: Start time in format "DD-MM-YYYY HH:MM" (24-hour format)
                   Example: "15-01-2025 14:00" for Jan 15 at 2 PM
        duration_minutes: Meeting duration in minutes (e.g., 60 for 1 hour)
        attendees: Comma-separated email addresses (e.g., "alice@example.com, bob@example.com")
        description: Optional meeting description/agenda
        timezone: Timezone for the meeting (default: Asia/Kolkata)
    
    Returns:
        String with meeting details and calendar link
    
    Example:
        schedule_meeting(
            "Q4 Project Review",
            "15-01-2025 14:00",
            60,
            "colleague@company.com",
            "Review Q4 deliverables and plan for Q1"
        )
    """
    if not _calendar_service:
        return "Error: Calendar service not initialized. Call initialize_tools() first."
    
    try:
        # print(f"📆 Scheduling meeting: {title}")
        
        # Parse start time
        tz = pytz.timezone(timezone)
        start_dt = datetime.strptime(start_time, "%d-%m-%Y %H:%M")
        start_dt = tz.localize(start_dt)
        
        # Calculate end time
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Parse attendees
        attendee_list = [{"email": email.strip()} for email in attendees.split(",")]
        
        print(f"   Start: {start_dt.strftime('%d-%m-%Y %I:%M %p')}")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Attendees: {', '.join([a['email'] for a in attendee_list])}")
        
        # Create event
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': timezone,
            },
            'attendees': attendee_list,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 30},  # 30 min before
                ],
            },
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meeting-{start_time.replace(' ', '-')}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }
        
        # Insert event
        created_event = _calendar_service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1  # Enable Google Meet link
        ).execute()
        
        # Extract details
        event_link = created_event.get('htmlLink', 'N/A')
        meet_link = created_event.get('hangoutLink', 'N/A')
        
        result = f"""✅ Meeting scheduled successfully!

Title: {title}
When: {start_dt.strftime('%A, %B %d, %Y at %I:%M %p')} ({timezone})
Duration: {duration_minutes} minutes
Attendees: {', '.join([a['email'] for a in attendee_list])}

Calendar link: {event_link}
Google Meet: {meet_link}

Calendar invitations have been sent to all attendees."""
        
        print(f"   ✓ Meeting created: {event_link}")
        return result
    
    except HttpError as e:
        error_msg = f"Calendar API error: {e}"
        print(f"   ✗ {error_msg}")
        return error_msg
    except ValueError as e:
        error_msg = f"Invalid date/time format: {e}. Use 'DD-MM-YYYY HH:MM' format."
        print(f"   ✗ {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Error scheduling meeting: {str(e)}"
        print(f"   ✗ {error_msg}")
        return error_msg

@tool
def send_email_reply(
    recipient: str,
    subject: str,
    body: str,
    draft_preview: str = ""
) -> str:
    """
    Send an email reply (DANGEROUS - requires HITL approval).
    
    Args:
        recipient: Email address of recipient
        subject: Email subject line
        body: Email body content
        draft_preview: Formatted preview (optional)
    
    Returns:
        Confirmation message
    
    Note: This is a simulated tool. In production, this would use Gmail API's send.
    """
    if not _gmail_service:
        return "Error: Gmail service not initialized."
    
    print(f"📤 SENDING EMAIL")
    print(f"   To: {recipient}")
    print(f"   Subject: {subject}")
    
    try:
        # In production, you would actually send via Gmail API:
        # from email.mime.text import MIMEText
        # import base64
        # 
        # message = MIMEText(body)
        # message['to'] = recipient
        # message['subject'] = subject
        # raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        # 
        # _gmail_service.users().messages().send(
        #     userId='me',
        #     body={'raw': raw}
        # ).execute()
        
        # For now, simulate sending
        print(f"   ✓ Email sent successfully (SIMULATED)")
        
        return f"""✅ Email sent successfully!

To: {recipient}
Subject: {subject}

The email has been delivered."""
        
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(f"   ✗ {error_msg}")
        return error_msg


@tool
def draft_email_reply(
    recipient: str,
    subject: str,
    body_content: str,
    original_subject: str = ""
) -> str:
    """
    Draft an email reply with professional formatting.
    
    This tool creates a properly formatted email draft but does NOT send it.
    The draft will need human approval before sending.
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        body_content: Main content of the email
        original_subject: Optional - subject of email being replied to
    
    Returns:
        Formatted email draft as a string
    
    Example:
        draft_email_reply(
            "colleague@company.com",
            "Re: Q4 Project Meeting",
            "I'm available Tuesday at 2pm or Wednesday at 10am. Let me know what works!"
        )
    """
    print(f"✍️  Drafting email to {recipient}")
    
    try:
        # Add "Re:" prefix if replying
        if original_subject and not subject.startswith("Re:"):
            if subject.lower() == original_subject.lower():
                subject = f"Re: {original_subject}"
        
        # Format the email
        draft = f"""To: {recipient}
Subject: {subject}

{body_content}

Best regards"""
        
        print(f"   ✓ Draft created ({len(body_content)} characters)")
        return draft
    
    except Exception as e:
        error_msg = f"Error creating draft: {str(e)}"
        print(f"   ✗ {error_msg}")
        return error_msg


# Tool list for easy import
def get_google_tools():
    """Returns list of all Google tools"""
    return [
        check_calendar,
        schedule_meeting,
        draft_email_reply,
        send_email_reply 
    ]