from react_agent import process_email
import os
from dotenv import load_dotenv

load_dotenv()

def demo_agent():
    """Demonstrate the email assistant agent with sample emails"""
    
    print("🤖 Email Assistant Agent - Milestone 1 Demo")
    print("=" * 50)
    
    # Sample emails to demonstrate different triage decisions
    sample_emails = [
        {
            "subject": "Meeting request for project discussion",
            "sender": "john.doe@company.com",
            "content": "Hi, I'd like to schedule a meeting next week to discuss the new project requirements. Are you available Tuesday or Wednesday afternoon?"
        },
        {
            "subject": "URGENT: Production server down",
            "sender": "alerts@monitoring.com", 
            "content": "Critical alert: Production server web-01 is not responding. Database connections failing. Immediate attention required."
        },
        {
            "subject": "Weekly newsletter - Industry updates",
            "sender": "newsletter@techindustry.com",
            "content": "Here are this week's top technology industry updates and trends you should know about..."
        }
    ]
    
    for i, email in enumerate(sample_emails, 1):
        print(f"\n📧 Email {i}:")
        print(f"Subject: {email['subject']}")
        print(f"From: {email['sender']}")
        print(f"Content: {email['content'][:100]}...")
        
        print("\n🔄 Processing through agent...")
        
        try:
            result = process_email(
                email_subject=email['subject'],
                email_sender=email['sender'],
                email_content=email['content']
            )
            
            print(f"📋 Triage Decision: {result['triage_decision'].upper()}")
            print(f"🧠 Reasoning: {result['reasoning']}")
            
            if result['tools_used']:
                print(f"🔧 Tools Used: {', '.join(result['tools_used'])}")
            
            if result['triage_decision'] == 'respond':
                print(f"📝 Generated Response:\n{result['response_content']}")
            else:
                print(f"📝 Action: {result['response_content']}")
                
        except Exception as e:
            print(f"❌ Error processing email: {str(e)}")
        
        print("-" * 50)

def interactive_mode():
    """Interactive mode for testing custom emails"""
    
    print("\n🔧 Interactive Mode - Test Your Own Emails")
    print("=" * 50)
    
    while True:
        print("\nEnter email details (or 'quit' to exit):")
        
        subject = input("Subject: ").strip()
        if subject.lower() == 'quit':
            break
            
        sender = input("Sender: ").strip()
        if sender.lower() == 'quit':
            break
            
        content = input("Content: ").strip()
        if content.lower() == 'quit':
            break
        
        print("\n🔄 Processing...")
        
        try:
            result = process_email(
                email_subject=subject,
                email_sender=sender,
                email_content=content
            )
            
            print(f"\n📋 Results:")
            print(f"Triage: {result['triage_decision'].upper()}")
            print(f"Reasoning: {result['reasoning']}")
            
            if result['tools_used']:
                print(f"Tools Used: {', '.join(result['tools_used'])}")
            
            print(f"Output: {result['response_content']}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Check environment setup
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: Please set GOOGLE_API_KEY in .env file")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Add to .env file: GOOGLE_API_KEY=your_key_here")
        exit(1)
    
    print("Choose mode:")
    print("1. Demo with sample emails")
    print("2. Interactive mode")
    print("3. Both")
    
    choice = input("Enter choice (1, 2, or 3): ").strip()
    
    if choice in ["1", "3"]:
        demo_agent()
    
    if choice in ["2", "3"]:
        interactive_mode()
    
    print("\n✅ Demo completed!")