import os
from typing import Dict, Any, List
from datetime import datetime

class MockLLM:
    """Mock LLM for demonstration when API quota is exhausted."""
    
    def invoke(self, messages):
        content = messages[0].content.lower()
        
        # Mock triage responses
        if "triage" in content:
            if any(word in content for word in ["spam", "winner", "congratulations", "newsletter"]):
                return MockResponse("ignore: This appears to be spam or promotional content")
            elif any(word in content for word in ["urgent", "server down", "critical", "legal", "confidential"]):
                return MockResponse("notify_human: This requires immediate human attention")
            else:
                return MockResponse("respond: This can be handled automatically")
        
        # Mock reasoning responses
        elif "processing an email" in content:
            return MockResponse("USE_TOOL: read_calendar - I need to check availability for scheduling")
        
        # Mock completion responses
        else:
            return MockResponse("Email processed successfully with appropriate triage decision")

class MockResponse:
    def __init__(self, content):
        self.content = content

class MockEmailAgent:
    """Mock version of EmailAgent for demonstration."""
    
    def __init__(self):
        self.llm = MockLLM()
    
    def process_email(self, email_content: str, sender: str = "", subject: str = "") -> Dict[str, Any]:
        """Process email with mock responses."""
        
        # Mock triage
        triage_prompt = f"Triage email from {sender}: {email_content}"
        triage_response = self.llm.invoke([MockMessage(triage_prompt)])
        
        if "ignore:" in triage_response.content:
            decision = "ignore"
        elif "notify_human:" in triage_response.content:
            decision = "notify_human"
        else:
            decision = "respond"
        
        result = {
            "email_content": email_content,
            "sender": sender,
            "subject": subject,
            "triage_decision": decision,
            "reasoning": triage_response.content,
            "messages": [
                {"role": "system", "content": f"Triage: {decision}"},
                {"role": "assistant", "content": "Mock processing completed"}
            ]
        }
        
        return result

class MockMessage:
    def __init__(self, content):
        self.content = content

def test_mock_agent():
    """Test the mock email agent."""
    
    agent = MockEmailAgent()
    
    test_emails = [
        {
            "content": "Hi, I'd like to schedule a meeting next week to discuss the project proposal.",
            "sender": "client@company.com",
            "subject": "Meeting Request - Project Discussion"
        },
        {
            "content": "CONGRATULATIONS! You've won $1,000,000! Click here to claim your prize!",
            "sender": "noreply@spam.com",
            "subject": "You're a WINNER!"
        },
        {
            "content": "The server is down and customers can't access our website. This is urgent!",
            "sender": "ops@company.com",
            "subject": "URGENT: Server Outage"
        }
    ]
    
    print("Testing Mock Email Agent (API Quota Exhausted - Using Mock Responses)")
    print("=" * 70)
    
    for i, email in enumerate(test_emails, 1):
        print(f"\nTest Email {i}:")
        print(f"From: {email['sender']}")
        print(f"Subject: {email['subject']}")
        print(f"Content: {email['content']}")
        
        result = agent.process_email(
            email_content=email['content'],
            sender=email['sender'],
            subject=email['subject']
        )
        
        print(f"\nTriage Decision: {result.get('triage_decision', 'Unknown')}")
        print(f"Reasoning: {result.get('reasoning', 'No reasoning provided')}")
        print("-" * 50)
    
    print("\nMOCK DEMONSTRATION COMPLETE")
    print("Note: Replace with real API key when quota is available")

if __name__ == "__main__":
    test_mock_agent()