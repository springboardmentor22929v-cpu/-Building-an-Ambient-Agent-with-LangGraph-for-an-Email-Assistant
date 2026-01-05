from typing import Dict, Any


def read_calendar(range_days: int = 7):
    """Mock calendar read."""
    return [
        {"id": "evt-1", "title": "Team sync", "start": "2026-01-04T10:00:00"},
        {"id": "evt-2", "title": "1:1 with manager", "start": "2026-01-05T15:00:00"},
    ]


def notify_human(email: Dict, note: str = "Automated triage: please review.") -> Dict[str, Any]:
    """Mock notification: returns status and metadata."""
    return {"status": "notified", "email_id": email.get('id'), "note": note}


def send_response(email: Dict, response_text: str) -> Dict[str, Any]:
    """Mock send: in real system this would call Gmail API and return a message id."""
    return {"status": "sent", "to": email.get('from'), "response_text": response_text}
