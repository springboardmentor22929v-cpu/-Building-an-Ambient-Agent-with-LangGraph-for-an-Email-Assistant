from src.agents.state import EmailAgentState
from src.tools.google_tools import get_google_tools


def execute_action_node(state: EmailAgentState) -> EmailAgentState:
    """
    Execute the approved action.
    
    This runs after human approval in HITL.
    """
    print("\n⚙️  EXECUTING ACTION")
    
    pending_action = state.get("pending_action")
    
    if not pending_action:
        print("   No action to execute")
        return state
    
    action_type = pending_action.get("action_type")
    action_args = pending_action.get("args", {})
    
    # Check if human edited the action
    if state.get("human_feedback"):
        print(f"   📝 Using human-edited version")
        # Update args with human edits
        action_args.update(state.get("human_feedback", {}))
    
    # Get tools
    tools = get_google_tools()
    tool_dict = {tool.name: tool for tool in tools}
    
    # Find and execute the tool
    if action_type in tool_dict:
        print(f"   🛠️  Executing: {action_type}")
        print(f"   Args: {action_args}")
        
        try:
            tool = tool_dict[action_type]
            result = tool.invoke(action_args)
            
            print(f"   ✓ Action completed successfully")
            
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
    else:
        print(f"   ✗ Unknown action type: {action_type}")
        
        return {
            **state,
            "execution_status": "unknown_action"
        }