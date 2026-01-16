import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes - what permissions we need
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """
    Authenticates with Gmail API and returns service object.
    
    On first run, opens browser for OAuth consent.
    Subsequent runs use saved token.
    """
    creds = None
    
    # Check if we have a saved token
    if os.path.exists('token.pickle'):
        print("📂 Loading saved credentials...")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth flow...")
            print("   A browser window will open for authentication.")
            
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "❌ credentials.json not found!\n"
                    "   Download it from Google Cloud Console:\n"
                    "   1. Go to APIs & Services → Credentials\n"
                    "   2. Download OAuth 2.0 Client ID JSON\n"
                    "   3. Save as 'credentials.json' in project root"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', 
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next time
        print("💾 Saving credentials...")
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    print("✅ Authentication successful!")
    
    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service


def test_connection():
    """Test if Gmail connection works"""
    try:
        service = authenticate_gmail()
        
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        
        print(f"\n✅ Connected to Gmail!")
        print(f"   Email: {profile['emailAddress']}")
        print(f"   Total messages: {profile['messagesTotal']}")
        
        return service
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return None


if __name__ == "__main__":
    # Test authentication
    test_connection()