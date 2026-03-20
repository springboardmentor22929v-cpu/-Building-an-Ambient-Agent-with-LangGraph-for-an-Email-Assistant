"""
Execute Action Node
Executes the approved action after HITL approval.
"""

from typing import Any, Dict, Optional

# Import from state.py
from state import EmailAgentState

# Import real tools
from real_tools import get_google_tools, initialize_tools
from gmail_auth import get_google_services


# -------------------------
# Execute Action Node
# -------------------------
def execute_action_node(state: EmailAgentState) -> EmailAgentState:
    """
    Execute the approved action.

    This runs AFTER human approval in the HITL flow.
    Uses pending_action with top-level fields: action_type, to, subject, body
    """
    print("\n⚙️  EXECUTING ACTION")

    pending_action = state.get("pending_action")

    if not pending_action:
        print("   No pending action found")
        return {
            **state,
            "execution_status": "no_action"
        }

    action_type = pending_action.get("action_type")
    
    # Extract top-level fields from pending_action (new structure)
    # Also check draft_reply for human edits in Studio
    action_args = {
        "to": pending_action.get("to", ""),
        "subject": pending_action.get("subject", ""),
        "body": pending_action.get("body", state.get("draft_reply", "")),
    }

    if not action_args["body"]:
        # Fallback to draft_reply if body is empty
        action_args["body"] = state.get("draft_reply", "")

    if not action_type:
        print("   ✗ Missing action_type")
        return {
            **state,
            "execution_status": "missing_action_type"
        }

    # -------------------------
    # Apply human edits (if any)
    # -------------------------
    if state.get("human_feedback"):
        print("   📝 Using human-edited arguments")
        # Allow human to edit to, subject, body
        action_args = {
            **action_args,
            **state["human_feedback"]
        }

    # -------------------------
    # Initialize Google services
    # -------------------------
    gmail_service, calendar_service = get_google_services()
    initialize_tools(gmail_service, calendar_service)

    # -------------------------
    # Load tools
    # -------------------------
    tools = get_google_tools()
    tool_dict = {tool.name: tool for tool in tools}

    print("   Available tools:", list(tool_dict.keys()))

    # -------------------------
    # Execute tool
    # -------------------------
    if action_type not in tool_dict:
        print(f"   ✗ Unknown action type: {action_type}")
        return {
            **state,
            "execution_status": "unknown_action"
        }

    print(f"   🛠️  Executing tool: {action_type}")
    print(f"   Args: {action_args}")

    try:
        tool = tool_dict[action_type]
        result = tool.invoke(action_args)

        print("   ✓ Action completed successfully")

        return {
            **state,
            "execution_result": result,
            "execution_status": "success"
        }

    except Exception as e:
        print(f"   ✗ Execution failed: {e}")

        return {
            **state,
            "execution_result": str(e),
            "execution_status": "failed"
        }


# -------------------------
# Local Test (REMOVE in production)
# -------------------------
if __name__ == "__main__":
    test_state: EmailAgentState = {
        "pending_action": {
            "action_type": "send_email",  # MUST match tool.name
            "to": "anjalik150904@gmail.com",
            "subject": "HITL Test Email",
            "body": "Hello from execute_action_node"
        },
        # Uncomment to simulate human edits
        # "human_feedback": {
        #     "subject": "Edited Subject by Human"
        # }
    }

    final_state = execute_action_node(test_state)

    print("\n📦 FINAL STATE")
    print(final_state)

