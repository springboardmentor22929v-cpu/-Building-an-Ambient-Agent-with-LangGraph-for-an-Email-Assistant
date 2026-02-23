import os
import base64
import json
import re
from html import unescape
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.message import EmailMessage

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def strip_html(html_text):
    """Convert HTML to readable plain text."""
    text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def extract_body(payload):
    """Recursively extract email body — prefer text/plain, fallback to text/html."""
    plain_data = ""
    html_data = ""

    if 'parts' in payload:
        for part in payload['parts']:
            mime = part.get('mimeType', '')
            if mime == 'text/plain':
                plain_data = part['body'].get('data', '')
            elif mime == 'text/html':
                html_data = part['body'].get('data', '')
            elif mime.startswith('multipart/'):
                result = extract_body(part)
                if result:
                    return result
    else:
        mime = payload.get('mimeType', '')
        data = payload.get('body', {}).get('data', '')
        if mime == 'text/plain':
            plain_data = data
        elif mime == 'text/html':
            html_data = data

    if plain_data:
        return base64.urlsafe_b64decode(plain_data).decode('utf-8', errors='replace')
    elif html_data:
        raw_html = base64.urlsafe_b64decode(html_data).decode('utf-8', errors='replace')
        return strip_html(raw_html)
    return ""


def get_gmail_service():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def get_latest_email():
    """Fetch the single most recent email and save to latest_email.json."""
    service = get_gmail_service()

    results = service.users().messages().list(
        userId='me',
        labelIds=['CATEGORY_PERSONAL'],
        maxResults=1
    ).execute()

    messages = results.get('messages', [])
    if not messages:
        print("No emails found.")
        return None

    msg = service.users().messages().get(
        userId='me',
        id=messages[0]['id'],
        format='full'
    ).execute()

    headers = msg['payload']['headers']
    sender = subject = ""

    for h in headers:
        if h['name'] == 'From':
            sender = h['value']
        if h['name'] == 'Subject':
            subject = h['value']

    body = extract_body(msg['payload'])

    email_data = {
        "from": sender,
        "subject": subject,
        "body": body
    }

    with open("latest_email.json", "w", encoding="utf-8") as f:
        json.dump(email_data, f, indent=4)

    print("\n📧 Email extracted and saved to latest_email.json")
    return email_data


def get_latest_emails(max_results=5):
    """Fetch the latest N emails from inbox. Returns a list of dicts."""
    service = get_gmail_service()

    results = service.users().messages().list(
        userId='me',
        labelIds=['CATEGORY_PERSONAL'],
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId='me',
            id=msg_ref['id'],
            format='full'
        ).execute()

        headers = msg['payload']['headers']
        sender = subject = ""
        for h in headers:
            if h['name'] == 'From':
                sender = h['value']
            if h['name'] == 'Subject':
                subject = h['value']

        body = extract_body(msg['payload'])

        emails.append({
            "msg_id": msg_ref['id'],
            "sender": sender,
            "subject": subject,
            "body": body[:2000]
        })

    return emails


def send_gmail_message(to: str, subject: str, body: str):
    """
    Send an email message via Gmail.
    """
    service = get_gmail_service()
    
    message = EmailMessage()
    message.set_content(body)
    message["To"] = to
    message["Subject"] = subject
    
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    create_message = {
        'raw': encoded_message
    }
    
    sent_message = service.users().messages().send(userId="me", body=create_message).execute()
    return sent_message


if __name__ == "__main__":
    get_latest_email()