# tools_langgraph.py
"""
Milestone 2 – LangGraph tool bindings
"""

from langchain_core.tools import tool
from m2_tools import (
    check_calendar_availability,
    schedule_meeting,
    schedule_meeting,
    draft_email_reply,
    send_email
)

# --------------------------------------------------
# Tool: Check calendar
# --------------------------------------------------
@tool
def calendar_tool(date: str, time: str) -> str:
    """Check calendar availability for a given date and time."""
    return check_calendar_availability(date, time)


# --------------------------------------------------
# Tool: Schedule meeting
# --------------------------------------------------
@tool
def meeting_scheduler_tool(date: str, time: str, with_person: str) -> str:
    """Schedule a meeting with a person."""
    return schedule_meeting(date, time, with_person)


# --------------------------------------------------
# Tool: Draft email
# --------------------------------------------------
@tool
def email_drafting_tool(subject: str, body: str) -> str:
    """Draft a professional email reply."""
    return draft_email_reply(subject, body)


# --------------------------------------------------
# Tool: Send email
# --------------------------------------------------
@tool
def email_sender_tool(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return send_email(to, subject, body)


# --------------------------------------------------
# Export tools as a list
# --------------------------------------------------
TOOLS = [
    calendar_tool,
    meeting_scheduler_tool,
    email_drafting_tool,
    email_sender_tool
]
