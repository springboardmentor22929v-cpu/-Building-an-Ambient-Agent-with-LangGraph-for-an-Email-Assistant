from state import AgentState
from tools.dangerous_tools import send_email
from tools.safe_tools import read_calendar


def execute_node(state: AgentState) -> AgentState:
    print("\n⚙️ EXECUTING ACTION")

    pending_action = state.get("pending_action")

    if not pending_action:
        print("   No action to execute")
        return state

    action_type = pending_action.get("action_type")
    action_args = pending_action.get("args", {}).copy()

    # ===== Handle Human Edit =====
    if state.get("human_decision") == "edit" and state.get("human_feedback"):
        print("   📝 Using human-edited version")

        edited_body = state.get("human_feedback")

        if edited_body:
            action_args["body"] = edited_body
            action_args["draft_preview"] = (
                f"Subject: {action_args.get('subject', '')}\n\n{edited_body}"
            )

    # ===== Execute Tool =====
    try:
        if action_type == "send_email":
            result = send_email(action_args.get("body"))

        elif action_type == "read_calendar":
            result = read_calendar()

        else:
            print(f"   ✗ Unknown action type: {action_type}")
            return {
                **state,
                "execution_status": "unknown_action"
            }

        print("   ✓ Action executed successfully")

        return {
            **state,
            "execution_result": result,
            "execution_status": "success"
        }

    except Exception as e:
        error_msg = str(e)
        print(f"   ✗ Execution failed: {error_msg}")

        return {
            **state,
            "execution_result": error_msg,
            "execution_status": "failed"
        }
