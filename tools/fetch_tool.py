# tools/fetch_tool.py

from langchain_core.tools import tool
from googleapiclient.discovery import build
from tools.real_tools import get_google_creds

@tool
def fetch_unread_emails() -> str:
    """
    Checks for new UNREAD emails, extracts them, and 
    IMMEDIATELY marks them as READ so they are not processed twice.
    """
    # 1. Get Credentials (re-using the logic from real_tools)
    creds = get_google_creds()
    if not creds: return "Authentication Failed."
    
    service = build('gmail', 'v1', credentials=creds)
    
    try:
        # 2. Ask Google for unread emails
        results = service.users().messages().list(
            userId='me', 
            labelIds=['INBOX'], 
            q='is:unread', 
            maxResults=1   # Fetch up to 5 emails
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return "📭 No new unread emails found."
        
        email_summary = "📥 UNREAD EMAILS FOUND:\n"
        
        for msg in messages:
            # 3. Get the email content
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = txt['payload']
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            snippet = txt.get('snippet', '')
            
            # ---------------------------------------------------------
            # 4. CRITICAL STEP: MARK AS READ
            # This removes the 'UNREAD' label so the bot ignores it next time.
            # ---------------------------------------------------------
            service.users().messages().modify(
                userId='me',
                id=msg['id'],
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            print(f"✅ Marked email '{subject}' as READ.")
            
            # Add to summary
            email_summary += f"- [From: {sender}] Subject: {subject} | Body: {snippet}\n"
            
        return email_summary

    except Exception as e:
        return f"❌ Error fetching emails: {e}"