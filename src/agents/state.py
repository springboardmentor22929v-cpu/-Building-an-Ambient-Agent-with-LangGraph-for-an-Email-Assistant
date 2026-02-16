from typing import TypedDict, Literal, Optional

class EmailAgentState(TypedDict):
    # ===== INPUT (Email Data) =====
    email_id: str
    email_from: str
    email_to: str  
    email_subject: str
    email_body: str
    
    # ===== TRIAGE OUTPUTS =====
    triage_decision: Literal["ignore", "notify_human", "respond"]
    triage_reasoning: str
    
    # ===== REACT AGENT =====
    messages: list
    
    # ===== HITL =====
    pending_action: Optional[dict]
    requires_approval: bool
    human_decision: Optional[Literal["approve", "deny", "edit"]]
    human_feedback: Optional[str]
    
    # ===== MEMORY =====
    user_preferences: dict