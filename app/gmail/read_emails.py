from app.gmail.gmail_client import get_gmail_service
from app.gmail.body_extractor import extract_email_body


def read_latest_emails(max_results=10):
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        message = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        # ---- Subject ----
        subject = ""
        for h in message["payload"]["headers"]:
            if h["name"] == "Subject":
                subject = h["value"]
                break

        # ---- Full Body (fixed) ----
        body = extract_email_body(message["payload"])

        emails.append({
            "subject": subject,
            "body": body
        })

    return emails
