from langchain.tools import tool
from datetime import datetime, timedelta
from typing import Optional
import pytz
from googleapiclient.errors import HttpError
import base64
from email.message import EmailMessage

# -------------------------------------------------
# Global services (initialized externally)
# -------------------------------------------------
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


# -------------------------------------------------
# CALENDAR TOOLS
# -------------------------------------------------
@tool
def check_calendar(
    start_date: str,
    end_date: str,
    timezone: str = "Asia/Kolkata"
) -> str:
    """Check calendar for available time slots."""
    if not _calendar_service:
        return "Error: Calendar service not initialized."

    try:
        tz = pytz.timezone(timezone)

        start_dt = tz.localize(
            datetime.strptime(start_date, "%d-%m-%Y").replace(hour=9)
        )
        end_dt = tz.localize(
            datetime.strptime(end_date, "%d-%m-%Y").replace(hour=17)
        )

        body = {
            "timeMin": start_dt.isoformat(),
            "timeMax": end_dt.isoformat(),
            "timeZone": timezone,
            "items": [{"id": "primary"}]
        }

        freebusy = _calendar_service.freebusy().query(body=body).execute()
        busy_times = freebusy["calendars"]["primary"]["busy"]

        available_slots = []
        current = start_dt

        while current.date() <= end_dt.date():
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            hour = current.replace(hour=9)
            day_slots = []

            while hour.hour < 17:
                slot_end = hour + timedelta(hours=1)
                is_free = True

                for busy in busy_times:
                    b_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                    b_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                    if not (slot_end <= b_start or hour >= b_end):
                        is_free = False
                        break

                if is_free:
                    day_slots.append(
                        f"{hour.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}"
                    )

                hour = slot_end

            if day_slots:
                available_slots.append(
                    f"{current.strftime('%A %b %d')}: {', '.join(day_slots[:3])}"
                )

            current += timedelta(days=1)

        return (
            "Available time slots:\n" +
            "\n".join(f"  • {s}" for s in available_slots)
            if available_slots
            else "No available time slots found."
        )

    except Exception as e:
        return f"Error checking calendar: {e}"


@tool
def schedule_meeting(
    title: str,
    start_time: str,
    duration_minutes: int,
    attendees: str,
    description: str = "",
    timezone: str = "Asia/Kolkata"
) -> str:
    """Schedule a meeting on Google Calendar."""
    if not _calendar_service:
        return "Error: Calendar service not initialized."

    try:
        tz = pytz.timezone(timezone)
        start_dt = tz.localize(datetime.strptime(start_time, "%d-%m-%Y %H:%M"))
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        attendee_list = [{"email": a.strip()} for a in attendees.split(",")]

        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone},
            "attendees": attendee_list,
        }

        created = _calendar_service.events().insert(
            calendarId="primary",
            body=event
        ).execute()

        return f"✅ Meeting scheduled: {created.get('htmlLink')}"

    except Exception as e:
        return f"Error scheduling meeting: {e}"


# -------------------------------------------------
# EMAIL TOOLS
# -------------------------------------------------
@tool
def draft_email_reply(
    recipient: str,
    subject: str,
    body_content: str,
    original_subject: str = ""
) -> str:
    """Draft an email reply (SAFE – does not send)."""
    if original_subject and not subject.startswith("Re:"):
        subject = f"Re: {original_subject}"

    return f"""To: {recipient}
Subject: {subject}

{body_content}

Best regards
"""


@tool
def send_email(
    to: str,
    subject: str,
    body: str
) -> str:
    """
    🚨 DANGEROUS TOOL 🚨
    Sends an email using Gmail API.
    MUST be protected by HITL.
    """
    if not _gmail_service:
        return "Error: Gmail service not initialized."

    try:
        message = EmailMessage()
        message.set_content(body)
        message["To"] = to
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        _gmail_service.users().messages().send(
            userId="me",
            body={"raw": encoded_message}
        ).execute()

        return f"📧 Email sent successfully to {to}"

    except Exception as e:
        return f"Error sending email: {e}"


# -------------------------------------------------
# TOOL REGISTRY
# -------------------------------------------------
def get_google_tools():
    """Returns list of all Google tools"""
    return [
        check_calendar,
        schedule_meeting,
        draft_email_reply,
        send_email,   # 👈 NOW AVAILABLE
    ]

if __name__ == "__main__":
    print("Available tools:")
    for t in get_google_tools():
        print("-", t.name)
