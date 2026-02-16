from langchain.tools import tool
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pytz
from googleapiclient.errors import HttpError

# Global services (will be set when tools are initialized)
_gmail_service = None
_calendar_service = None
_tasks_service = None


def initialize_tools(gmail_service, calendar_service, tasks_service=None):
    """
    Initialize tools with authenticated Google services.
    Call this before using any tools.
    """
    global _gmail_service, _calendar_service, _tasks_service
    _gmail_service = gmail_service
    _calendar_service = calendar_service
    _tasks_service = tasks_service
    print("✅ Tools initialized with Google services")


# ──────────────────────────── READ EMAIL ────────────────────────────

@tool
def read_email(
    max_results: int = 5,
    query: str = "is:unread"
) -> str:
    """
    Fetch recent emails from Gmail inbox.  This is a SAFE tool – no approval needed.

    Args:
        max_results: Number of emails to retrieve (default 5)
        query: Gmail search query, e.g. "is:unread", "from:someone@example.com"

    Returns:
        A formatted string listing the fetched emails with From, Subject, and a snippet.
    """
    if not _gmail_service:
        return "Error: Gmail service not initialized. Call initialize_tools() first."

    try:
        results = _gmail_service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return "No emails found matching the query."

        import base64
        import re

        output_lines = []
        for idx, msg_meta in enumerate(messages, 1):
            msg = _gmail_service.users().messages().get(
                userId='me', id=msg_meta['id'], format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', '(no subject)')
            date = headers.get('Date', '')
            snippet = msg.get('snippet', '')

            output_lines.append(
                f"{idx}. From: {sender}\n"
                f"   Subject: {subject}\n"
                f"   Date: {date}\n"
                f"   Preview: {snippet[:120]}\n"
            )

        return "\n".join(output_lines)

    except HttpError as e:
        return f"Gmail API error: {e}"
    except Exception as e:
        return f"Error reading emails: {str(e)}"


# ──────────────────────────── CHECK CALENDAR ────────────────────────

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
    """
    if not _calendar_service:
        return "Error: Calendar service not initialized. Call initialize_tools() first."

    try:
        tz = pytz.timezone(timezone)

        start_datetime = datetime.strptime(start_date, "%d-%m-%Y")
        start_datetime = start_datetime.replace(hour=9, minute=0, second=0)
        start_datetime = tz.localize(start_datetime)

        end_datetime = datetime.strptime(end_date, "%d-%m-%Y")
        end_datetime = end_datetime.replace(hour=17, minute=0, second=0)
        end_datetime = tz.localize(end_datetime)

        body = {
            "timeMin": start_datetime.isoformat(),
            "timeMax": end_datetime.isoformat(),
            "timeZone": timezone,
            "items": [{"id": "primary"}]
        }

        freebusy = _calendar_service.freebusy().query(body=body).execute()
        busy_times = freebusy['calendars']['primary']['busy']

        available_slots = []
        current_day = start_datetime

        while current_day.date() <= end_datetime.date():
            if current_day.weekday() >= 5:
                current_day += timedelta(days=1)
                continue

            day_start = current_day.replace(hour=9, minute=0)
            day_end = current_day.replace(hour=17, minute=0)

            day_slots = []
            current_time = day_start

            while current_time < day_end:
                slot_end = current_time + timedelta(hours=1)

                is_free = True
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    if not (slot_end <= busy_start or current_time >= busy_end):
                        is_free = False
                        break

                if is_free:
                    day_slots.append(
                        f"{current_time.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}"
                    )

                current_time = slot_end

            if day_slots:
                day_name = current_day.strftime("%A %b %d")
                available_slots.append(f"{day_name}: {', '.join(day_slots[:3])}")

            current_day += timedelta(days=1)

        if available_slots:
            return "Available time slots:\n" + "\n".join(
                [f"  • {slot}" for slot in available_slots]
            )
        else:
            return "No available time slots found in the specified date range."

    except HttpError as e:
        return f"Calendar API error: {e}"
    except Exception as e:
        return f"Error checking calendar: {str(e)}"


# ──────────────────────────── SCHEDULE MEETING ──────────────────────

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
    Schedule a meeting on Google Calendar.  DANGEROUS – requires HITL approval.

    Args:
        title: Meeting title/subject
        start_time: Start time in format "DD-MM-YYYY HH:MM" (24-hour)
        duration_minutes: Meeting duration in minutes
        attendees: Comma-separated email addresses
        description: Optional meeting description/agenda
        timezone: Timezone for the meeting (default: Asia/Kolkata)

    Returns:
        String with meeting details and calendar link
    """
    if not _calendar_service:
        return "Error: Calendar service not initialized. Call initialize_tools() first."

    try:
        tz = pytz.timezone(timezone)
        start_dt = datetime.strptime(start_time, "%d-%m-%Y %H:%M")
        start_dt = tz.localize(start_dt)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        attendee_list = [{"email": email.strip()} for email in attendees.split(",")]

        event = {
            'summary': title,
            'description': description,
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': timezone},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': timezone},
            'attendees': attendee_list,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meeting-{start_time.replace(' ', '-')}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }

        created_event = _calendar_service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1
        ).execute()

        event_link = created_event.get('htmlLink', 'N/A')
        meet_link = created_event.get('hangoutLink', 'N/A')

        return (
            f"✅ Meeting scheduled successfully!\n\n"
            f"Title: {title}\n"
            f"When: {start_dt.strftime('%A, %B %d, %Y at %I:%M %p')} ({timezone})\n"
            f"Duration: {duration_minutes} minutes\n"
            f"Attendees: {', '.join(a['email'] for a in attendee_list)}\n\n"
            f"Calendar link: {event_link}\n"
            f"Google Meet: {meet_link}\n\n"
            f"Calendar invitations have been sent to all attendees."
        )

    except HttpError as e:
        return f"Calendar API error: {e}"
    except ValueError as e:
        return f"Invalid date/time format: {e}. Use 'DD-MM-YYYY HH:MM' format."
    except Exception as e:
        return f"Error scheduling meeting: {str(e)}"


# ──────────────────────────── SEND EMAIL (REAL) ─────────────────────

@tool
def send_email_reply(
    recipient: str,
    subject: str,
    body: str,
    draft_preview: str = ""
) -> str:
    """
    Send an email reply via Gmail API. DANGEROUS – requires HITL approval.

    Args:
        recipient: Email address of recipient
        subject: Email subject line
        body: Email body content
        draft_preview: Formatted preview (optional)

    Returns:
        Confirmation message
    """
    if not _gmail_service:
        return "Error: Gmail service not initialized."

    print(f"📤 SENDING EMAIL")
    print(f"   To: {recipient}")
    print(f"   Subject: {subject}")

    try:
        from email.mime.text import MIMEText
        import base64

        message = MIMEText(body)
        message['to'] = recipient
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        _gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        print(f"   ✓ Email sent successfully")

        return (
            f"✅ Email sent successfully!\n\n"
            f"To: {recipient}\n"
            f"Subject: {subject}\n\n"
            f"The email has been delivered."
        )

    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(f"   ✗ {error_msg}")
        return error_msg


# ──────────────────────────── DRAFT EMAIL ───────────────────────────

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
        original_subject: Optional – subject of email being replied to

    Returns:
        Formatted email draft as a string
    """
    print(f"✍️  Drafting email to {recipient}")

    try:
        if original_subject and not subject.startswith("Re:"):
            if subject.lower() == original_subject.lower():
                subject = f"Re: {original_subject}"

        draft = (
            f"To: {recipient}\n"
            f"Subject: {subject}\n\n"
            f"{body_content}\n\n"
            f"Best regards"
        )

        print(f"   ✓ Draft created ({len(body_content)} characters)")
        return draft

    except Exception as e:
        return f"Error creating draft: {str(e)}"


# ──────────────────────────── GOOGLE TASK ───────────────────────────

@tool
def create_google_task(
    title: str,
    notes: str = "",
    due: str = None
) -> str:
    """
    Create a new task in Google Tasks.

    Args:
        title: The title of the task
        notes: Optional notes or details
        due: Optional due date in RFC 3339 format

    Returns:
        Confirmation message with task details
    """
    if not _tasks_service:
        return "Error: Tasks service not initialized."

    try:
        task = {'title': title, 'notes': notes}
        if due:
            task['due'] = due

        result = _tasks_service.tasks().insert(
            tasklist='@default', body=task
        ).execute()

        return f"✅ Task created successfully!\nTitle: {result['title']}\nStatus: {result['status']}"

    except Exception as e:
        return f"Error creating task: {str(e)}"


# ──────────────────────────── TOOL REGISTRY ─────────────────────────

def get_safe_tools():
    """Returns list of safe tools (no approval needed)."""
    return [read_email, check_calendar, draft_email_reply, create_google_task]


def get_dangerous_tools():
    """Returns list of dangerous tools (require HITL approval)."""
    return [send_email_reply, schedule_meeting]


def get_google_tools():
    """Returns list of ALL Google tools."""
    return get_safe_tools() + get_dangerous_tools()