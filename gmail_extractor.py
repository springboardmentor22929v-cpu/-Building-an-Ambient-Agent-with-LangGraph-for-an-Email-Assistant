import os
import base64
from typing import List, Dict
import json
from typing import List, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from demo_agent import DemoEmailAgent

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailExtractor:
    def __init__(self):
        self.service = None
        self.email_agent = DemoEmailAgent()
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Load existing token
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail API connected successfully")
    
    def get_recent_emails(self, max_results: int = 10) -> List[Dict]:
        """Extract recent emails from Gmail"""
        if not self.service:
            self.authenticate()
        
        try:
            # Get message list
            results = self.service.users().messages().list(
                userId='me', 
                maxResults=max_results,
                q='is:unread'  # Only unread emails
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            print(f"📧 Extracting {len(messages)} unread emails...")
            
            for msg in messages:
                # Get full message
                message = self.service.users().messages().get(
                    userId='me', 
                    id=msg['id']
                ).execute()
                
                # Extract email data
                email_data = self._parse_email(message)
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"❌ Error extracting emails: {e}")
            return []
    
    def _parse_email(self, message: Dict) -> Dict:
        """Parse Gmail message to extract relevant data"""
        headers = message['payload'].get('headers', [])
        
        # Extract headers
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        
        # Extract body
        body = self._get_email_body(message['payload'])
        
        return {
            'id': message['id'],
            'sender': sender,
            'subject': subject,
            'content': body,
            'snippet': message.get('snippet', '')
        }
    
    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        elif payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body or payload.get('snippet', '')
    
    def process_gmail_emails(self, max_emails: int = 10):
        """Extract and process Gmail emails through triage system"""
        print("🚀 Starting Gmail Email Processing...")
        
        # Extract emails
        emails = self.get_recent_emails(max_emails)
        
        if not emails:
            print("📭 No unread emails found")
            return
        
        print(f"\n📊 Processing {len(emails)} emails through triage system...")
        print("-" * 60)
        
        results = []
        for i, email in enumerate(emails, 1):
            print(f"Processing email {i}/{len(emails)}: {email['subject'][:50]}...")
            
            # Process through email agent
            result = self.email_agent.process_email(
                email['content'],
                email['sender'],
                email['subject']
            )
            
            # Add Gmail metadata
            result['gmail_id'] = email['id']
            result['snippet'] = email['snippet']
            
            results.append(result)
            
            # Print result
            print(f"  Decision: {result['triage_decision']}")
            print(f"  Reasoning: {result['reasoning'][:100]}...")
            print()
        
        # Summary
        decisions = [r['triage_decision'] for r in results]
        summary = {
            'ignore': decisions.count('ignore'),
            'notify_human': decisions.count('notify_human'),
            'respond': decisions.count('respond')
        }
        
        print("📈 GMAIL PROCESSING SUMMARY")
        print("=" * 40)
        print(f"Total emails processed: {len(emails)}")
        print(f"Ignore: {summary['ignore']}")
        print(f"Notify Human: {summary['notify_human']}")
        print(f"Respond: {summary['respond']}")
        
        return results

def main():
    """Main function to run Gmail extraction and processing"""
    extractor = GmailExtractor()
    
    try:
        # Process recent Gmail emails
        results = extractor.process_gmail_emails(max_emails=5)
        
        # Save results
        if results:
            with open('gmail_processing_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to gmail_processing_results.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📋 Setup Required:")
        print("1. Enable Gmail API in Google Cloud Console")
        print("2. Download credentials.json file")
        print("3. Install: pip install google-auth google-auth-oauthlib google-api-python-client")

if __name__ == "__main__":
    main()
from email.mime.text import MIMEText
