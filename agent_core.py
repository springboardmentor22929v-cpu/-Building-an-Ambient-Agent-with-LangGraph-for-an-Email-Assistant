from typing import TypedDict, Literal, List, Dict, Any
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()

# Agent State
class AgentState(TypedDict):
    email_content: str
    email_subject: str
    email_sender: str
    triage_decision: Literal["ignore", "notify_human", "respond"]
    reasoning: str
    tools_used: List[str]
    response_content: str

# Triage Classification
class TriageResult(BaseModel):
    decision: Literal["ignore", "notify_human", "respond"]
    reasoning: str
    confidence: float

class TriageNode:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1
        )
    
    def classify_email(self, state: AgentState) -> AgentState:
        """Classify email into ignore, notify_human, or respond categories"""
        
        triage_prompt = f"""
You are an email triage assistant. Classify this email into one of three categories:

1. "ignore" - Spam, newsletters, automated notifications that don't need action
2. "notify_human" - Important emails requiring human judgment (urgent, sensitive, complex)
3. "respond" - Emails that can be handled with a standard response

Email Subject: {state['email_subject']}
Email Sender: {state['email_sender']}
Email Content: {state['email_content']}

Respond with your classification and brief reasoning. Be decisive and confident.

Format your response as:
DECISION: [ignore/notify_human/respond]
REASONING: [brief explanation]
CONFIDENCE: [0.0-1.0]
"""

        messages = [
            SystemMessage(content="You are a precise email classification system."),
            HumanMessage(content=triage_prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        lines = response.content.strip().split('\n')
        decision = "notify_human"  # default fallback
        reasoning = "Unable to parse response"
        confidence = 0.5
        
        for line in lines:
            if line.startswith("DECISION:"):
                decision = line.split(":", 1)[1].strip().lower()
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except:
                    confidence = 0.5
        
        state["triage_decision"] = decision
        state["reasoning"] = reasoning
        
        return state

# Mock Tools for ReAct Agent
class MockTools:
    @staticmethod
    def read_calendar(date: str = None) -> Dict[str, Any]:
        """Mock calendar tool - returns sample calendar data"""
        return {
            "events": [
                {"time": "09:00", "title": "Team Meeting", "duration": "1h"},
                {"time": "14:00", "title": "Client Call", "duration": "30m"}
            ],
            "availability": ["10:00-13:00", "15:00-17:00"]
        }
    
    @staticmethod
    def get_contact_info(name: str) -> Dict[str, Any]:
        """Mock contact lookup tool"""
        contacts = {
            "john": {"email": "john@company.com", "phone": "+1234567890"},
            "sarah": {"email": "sarah@company.com", "phone": "+1234567891"}
        }
        return contacts.get(name.lower(), {"error": "Contact not found"})