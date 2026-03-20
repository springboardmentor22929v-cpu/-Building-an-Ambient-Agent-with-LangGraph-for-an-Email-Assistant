"""
Human-in-the-Loop (HITL) Checkpoint Node
Studio-Compatible Version - No blocking input()
Decision is injected manually via LangGraph Studio UI.
Enhanced with Learning Support - When human edits, feedback is saved.
"""

from typing import Literal, Optional


# =====================================================
# Import EmailAgentState from state.py
# =====================================================

try:
    from state import EmailAgentState
except ImportError:
    # fallback so file can still run
    EmailAgentState = dict
    print(
        "\n⚠️ EmailAgentState not found in state.py.\n"
        "Using dict as fallback.\n"
    )


# =====================================================
# Tool Categories
# =====================================================

# Dangerous tools → require human approval
DANGEROUS_TOOLS = [
    "send_email",
    "schedule_meeting",
    "delete_email",
    "forward_email",
]

# Safe tools → auto execute
SAFE_TOOLS = [
    "check_calendar",
    "search_past_emails",
    "draft_email_reply",
]


# =====================================================
# HITL Checkpoint Node (Studio-Compatible)
# =====================================================

def hitl_checkpoint_node(state: EmailAgentState) -> dict:
    """
    In Studio, we DO NOT use input().
    Decision is injected manually via UI.
    
    This node simply returns an empty dict, allowing the graph
    to pause at the interrupt_before checkpoint.
    Studio will show the state and allow user to add hitl_decision.
    
    When human makes an "edit" decision, we capture the edited content
    in human_feedback for the memory node to learn from.
    """
    print("\n🚦 HITL CHECKPOINT - Waiting for human approval via Studio")
    
    # Check if human made a decision
    decision = state.get("hitl_decision")
    
    # Return empty dict - Studio handles the pause
    # The decision will be injected via state updates in Studio
    return {}


# =====================================================
# Routing After HITL
# =====================================================

def should_continue_after_hitl(
    state: EmailAgentState,
) -> Literal["execute", "end", "wait"]:
    """
    Routing after HITL checkpoint.
    
    execute → approved or edited
    end → denied
    """

    decision = state.get("hitl_decision")

    # Approved or edited
    if decision in ["approve", "edit"]:
        return "execute"

    # Denied or no decision
    return "end"


# =====================================================
# Process Human Edit (for learning)
# =====================================================

def process_human_edit(state: EmailAgentState) -> dict:
    """
    Process human edit and prepare for memory learning.
    This extracts the edited content from human_feedback.
    """
    decision = state.get("hitl_decision")
    
    if decision == "edit":
        # Get the edited draft from pending_action or draft_reply
        pending_action = state.get("pending_action", {})
        edited_body = pending_action.get("body", state.get("draft_reply", ""))
        
        # The human_feedback should contain the edits made by human
        # This will be used by memory node to learn
        return {
            "human_decision": "edit",
            "human_feedback": {
                "body": edited_body,
                "note": "Human edited the response"
            }
        }
    
    elif decision == "approve":
        return {"human_decision": "approve"}
    
    elif decision == "deny":
        return {"human_decision": "deny"}
    
    return {}


# =====================================================
# Test Run Support (so python HITL.py works)
# =====================================================

if __name__ == "__main__":
    print("\n✅ HITL module loaded successfully (Studio-compatible version)!")

