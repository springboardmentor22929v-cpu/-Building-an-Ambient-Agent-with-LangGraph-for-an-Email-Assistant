import os
from typing import Dict, Any, List, Literal
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Load environment variables
load_dotenv()

class EmailState(BaseModel):
    email_content: str = ""
    sender: str = ""
    subject: str = ""
    triage_decision: str = ""
    reasoning: str = ""
    messages: List[Dict[str, Any]] = []
    next_action: str = ""
    tool_results: Dict[str, Any] = {}

# Mock tools for the agent
@tool
def read_calendar(date: str = None) -> str:
    """Read calendar availability for a given date."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    return f"Calendar for {date}: Available 9-11 AM, Meeting 2-3 PM, Free after 4 PM"

@tool
def get_user_preferences() -> str:
    """Get user preferences for email handling."""
    return "User prefers: Brief responses, Schedule meetings for mornings, Auto-decline spam"

@tool
def draft_response(email_content: str, context: str = "") -> str:
    """Draft a response to an email."""
    return f"Draft response based on: {email_content[:100]}... Context: {context}"

class EmailAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1
        )
        self.tools = [read_calendar, get_user_preferences, draft_response]
        self.tool_node = ToolNode(self.tools)
        self.graph = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(dict)
        
        workflow.add_node("triage", self.triage_node)
        workflow.add_node("reason", self.reason_node)
        workflow.add_node("act", self.tool_node)
        workflow.add_node("complete", self.complete_node)
        
        workflow.set_entry_point("triage")
        
        workflow.add_conditional_edges(
            "triage",
            self.should_continue_after_triage,
            {
                "ignore": END,
                "notify_human": END,
                "respond": "reason"
            }
        )
        
        workflow.add_conditional_edges(
            "reason",
            self.should_use_tool,
            {
                "use_tool": "act",
                "complete": "complete"
            }
        )
        
        workflow.add_edge("act", "reason")
        workflow.add_edge("complete", END)
        
        return workflow.compile()
    
    def triage_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the email into ignore, notify_human, or respond categories."""
        
        triage_prompt = f"""
        You are an email triage assistant. Classify this email into one of three categories:
        
        1. "ignore" - Spam, newsletters, or unimportant emails
        2. "notify_human" - Important emails requiring human attention (urgent, sensitive, or complex)
        3. "respond" - Emails that can be handled automatically with a response
        
        Email Details:
        From: {state.get('sender', 'Unknown')}
        Subject: {state.get('subject', 'No Subject')}
        Content: {state.get('email_content', '')}
        
        Respond with only the category name and a brief reason.
        Format: CATEGORY: reason
        """
        
        response = self.llm.invoke([HumanMessage(content=triage_prompt)])
        
        # Parse the response
        response_text = response.content.strip()
        if "ignore:" in response_text.lower():
            decision = "ignore"
        elif "notify_human:" in response_text.lower():
            decision = "notify_human"
        elif "respond:" in response_text.lower():
            decision = "respond"
        else:
            # Default to notify_human for safety
            decision = "notify_human"
        
        state["triage_decision"] = decision
        state["reasoning"] = response_text
        state["messages"] = [{"role": "system", "content": f"Triage decision: {decision}. Reasoning: {response_text}"}]
        
        return state
    
    def reason_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Reason about what action to take next."""
        
        context = "\n".join([msg.get("content", "") for msg in state.get("messages", [])])
        
        reasoning_prompt = f"""
        You are processing an email that needs a response. Based on the context, decide what to do next.
        
        Email: {state.get('email_content', '')}
        Context: {context}
        
        Available tools:
        - read_calendar: Check calendar availability
        - get_user_preferences: Get user email preferences
        - draft_response: Create a draft response
        
        Choose ONE action:
        1. If you need more information, specify which tool to use: "USE_TOOL: tool_name"
        2. If you have enough information to complete the task: "COMPLETE: final_action"
        
        Be specific about what you need and why.
        """
        
        response = self.llm.invoke([HumanMessage(content=reasoning_prompt)])
        response_text = response.content.strip()
        
        state["messages"].append({"role": "assistant", "content": response_text})
        state["next_action"] = response_text
        
        return state
    
    def complete_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Complete the email processing task."""
        
        completion_prompt = f"""
        Based on all the information gathered, provide a final summary of actions taken for this email.
        
        Email: {state.get('email_content', '')}
        Triage Decision: {state.get('triage_decision', '')}
        Context: {state.get('messages', [])}
        Tool Results: {state.get('tool_results', {})}
        
        Provide a concise summary of what was accomplished.
        """
        
        response = self.llm.invoke([HumanMessage(content=completion_prompt)])
        
        state["messages"].append({"role": "assistant", "content": f"COMPLETED: {response.content}"})
        
        return state
    
    def should_continue_after_triage(self, state: Dict[str, Any]) -> str:
        """Determine the next step after triage."""
        return state.get("triage_decision", "notify_human")
    
    def should_use_tool(self, state: Dict[str, Any]) -> str:
        """Determine if a tool should be used or if the task is complete."""
        next_action = state.get("next_action", "").lower()
        
        if "use_tool:" in next_action:
            return "use_tool"
        elif "complete:" in next_action:
            return "complete"
        else:
            return "complete"
    
    def process_email(self, email_content: str, sender: str = "", subject: str = "") -> Dict[str, Any]:
        """Process a single email through the agent."""
        
        initial_state = {
            "email_content": email_content,
            "sender": sender,
            "subject": subject,
            "messages": [],
            "tool_results": {}
        }
        
        result = self.graph.invoke(initial_state)
        return result

# Test function
def test_agent():
    """Test the email agent with sample emails."""
    
    agent = EmailAgent()
    
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
    
    print("Testing Email Agent...")
    print("=" * 50)
    
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
        
        if result.get('messages'):
            print("Agent Messages:")
            for msg in result['messages'][-2:]:  # Show last 2 messages
                print(f"  - {msg.get('content', '')[:100]}...")
        
        print("-" * 50)

if __name__ == "__main__":
    test_agent()