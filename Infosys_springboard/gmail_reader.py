import os
import base64
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.message import EmailMessage

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

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
    service = get_gmail_service()

    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        maxResults=1
    ).execute()

    messages = results.get('messages', [])
    if not messages:
        print("No emails found.")
        return

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

    body = ""
    payload = msg['payload']

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                body = part['body'].get('data', '')
                break
    else:
        body = payload['body'].get('data', '')

    if body:
        body = base64.urlsafe_b64decode(body).decode('utf-8')

    email_data = {
        "from": sender,
        "subject": subject,
        "body": body
    }

    with open("latest_email.json", "w", encoding="utf-8") as f:
        json.dump(email_data, f, indent=4)

    print("\n📧 Email extracted and saved to latest_email.json")


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