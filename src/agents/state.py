from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages  

class EmailAgentState(TypedDict):
    """State that flows through the agent"""
    # Input
    email_id: str
    email_from: str
    email_subject: str
    email_body: str
    
    # Triage output
    triage_decision: Literal["ignore", "notify_human", "respond"]
    triage_reasoning: str
    
    # ReAct loop
    messages: Annotated[list, add_messages]  
    
    # Memory 
    user_preferences: dict