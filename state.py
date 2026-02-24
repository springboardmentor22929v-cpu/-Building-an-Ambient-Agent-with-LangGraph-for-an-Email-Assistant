from typing import TypedDict, Literal, Optional, Dict, List


class AgentState(TypedDict):
    # ===== INPUT =====
    email_id: Optional[str]
    email_from: str
    email_subject: str
    email_body: str

    # ===== TRIAGE =====
    triage_decision: Optional[Literal["ignore", "notify_human", "respond"]]
    triage_reasoning: Optional[str]

    # ===== REACT =====
    messages: Optional[List[Dict]]

    # ===== HITL =====
    pending_action: Optional[Dict]
    requires_approval: Optional[bool]
    human_decision: Optional[Literal["approve", "deny", "edit"]]
    human_feedback: Optional[Dict]

    # ===== EXECUTION =====
    execution_result: Optional[str]
    execution_status: Optional[str]

    # ===== MEMORY =====
    user_preferences: Dict
    memory_saved: Optional[bool]

    # ===== WORKFLOW =====
    workflow_id: Optional[str]
