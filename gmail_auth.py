import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Updated scopes - Gmail + Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
    'https://www.googleapis.com/auth/gmail.send',      # Send emails (for later)
    'https://www.googleapis.com/auth/calendar.readonly',  # Read calendar
    'https://www.googleapis.com/auth/calendar.events'     # Create events
]

def authenticate_google_services():
    """
    Authenticates with Google APIs (Gmail + Calendar).
    
    On first run, opens browser for OAuth consent.
    Subsequent runs use saved token.
    Returns:
        tuple: (gmail_service, calendar_service)
    """
    creds = None
    # Check for existing token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"❌ Refresh failed: {e}")
                print("   Falling back to full authentication...")
                creds = None
        if not creds:
            print("🔐 Starting OAuth flow...")
            print("   A browser window will open for authentication.")
            print("   ⚠️  You'll need to grant Calendar permissions this time.")
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "❌ credentials.json not found!\n"
                    "   Download it from Google Cloud Console:\n"
                    "   1. Go to APIs & Services → Credentials\n"
                    "   2. Download OAuth 2.0 Client ID JSON\n"
                    "   3. Save as 'credentials.json' in project root"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save credentials
        print("💾 Saving credentials...")
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    print("✅ Authentication successful!")
    # Build services
    gmail_service = build('gmail', 'v1', credentials=creds)
    calendar_service = build('calendar', 'v3', credentials=creds)
    
    return gmail_service, calendar_service

def get_google_services():
    """Get authenticated Google services (Gmail + Calendar)."""
    return authenticate_google_services()

def test_connection():
    """Test if Gmail and Calendar connections work"""
    try:
        gmail, calendar = authenticate_google_services()
        # Test Gmail
        profile = gmail.users().getProfile(userId='me').execute()
        print(f"\n✅ Gmail Connected!")
        print(f"   Email: {profile['emailAddress']}")
        print(f"   Total messages: {profile['messagesTotal']}")
        # Test Calendar
        cal_list = calendar.calendarList().list().execute()
        print(f"\n✅ Calendar Connected!")
        print(f"   Found {len(cal_list.get('items', []))} calendars")
        for cal in cal_list.get('items', [])[:3]:
            print(f"      • {cal['summary']}")
        
        return gmail, calendar
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return None, None

if __name__ == "__main__":
    # Test authentication
    test_connection()
