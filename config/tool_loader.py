# config/tool_loader.py
import os
import email.utils
from dotenv import load_dotenv
from googleapiclient.discovery import build
from tools.real_tools import get_google_creds

# Import Tools
from tools.real_tools import write_email as real_write, check_calendar as real_cal
from tools.fetch_tool import fetch_unread_emails as real_fetch
from tools.mock_tools import write_email as mock_write, check_calendar as mock_cal, fetch_unread_emails as mock_fetch

load_dotenv()

def get_gmail_profile_name():
    """
    Auto-detects the user's signature name from their Gmail history.
    """
    # Check Mode
    mode = os.getenv("USE_REAL_TOOLS", "false").lower()
    if mode != "true":
        return "Mock User"

    try:
        creds = get_google_creds()
        if not creds: return "Ambient User"
        
        service = build('gmail', 'v1', credentials=creds)
        
        # STRATEGY 1: Check the 'Sent' box for the Real Display Name
        results = service.users().messages().list(userId='me', q='label:SENT', maxResults=1).execute()
        messages = results.get('messages', [])
        
        if messages:
            msg = service.users().messages().get(
                userId='me', 
                id=messages[0]['id'], 
                format='metadata', 
                metadataHeaders=['From']
            ).execute()
            
            headers = msg.get('payload', {}).get('headers', [])
            for header in headers:
                if header['name'] == 'From':
                    from_val = header['value']
                    name, addr = email.utils.parseaddr(from_val)
                    if name:
                        print(f"👤 [SYSTEM] Auto-Detected Signature: {name}")
                        return name

        # STRATEGY 2: Fallback to Email Username
        profile = service.users().getProfile(userId='me').execute()
        email_addr = profile.get('emailAddress', '')
        
        if email_addr:
            name_part = email_addr.split('@')[0]
            formatted_name = name_part.replace('.', ' ').title()
            print(f"👤 [SYSTEM] Auto-Detected Signature: {formatted_name}")
            return formatted_name
            
        return "Ambient User"

    except Exception as e:
        print(f"⚠️ Could not fetch Gmail Profile: {e}")
        return "Ambient User"

def get_active_tools():
    """
    Returns the correct list of tools for the AGENT to use.
    CRITICAL FIX: We DO NOT include 'fetch_unread_emails' here.
    The Agent should only Reply or Check Calendar. It should not Fetch.
    """
    mode = os.getenv("USE_REAL_TOOLS", "false").lower()
    
    if mode == "true":
        print("🔧 [SYSTEM] Mode: REAL (Agent has: Write Email, Check Calendar)")
        # REMOVED real_fetch FROM THIS LIST 👇
        return [real_write, real_cal]
    else:
        print("🔧 [SYSTEM] Mode: MOCK (Agent has: Write Email, Check Calendar)")
        # REMOVED mock_fetch FROM THIS LIST 👇
        return [mock_write, mock_cal]