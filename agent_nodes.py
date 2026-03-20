"""
Agent nodes for LangGraph
"""

def agent_node(state):
    text = state.get("user_input", "")

    draft = f"""
Hi,

This is regarding: {text}

Please let me know if you need anything else.

Best regards,
AI Assistant
"""

    return {
        "agent_output": draft,
        "pending_action": {
            "action_type": "send_email_reply",
            "args": {
                "recipient": "alice@company.com",
                "subject": "Project Update",
                "draft_preview": draft
            }
        },
        "requires_approval": True
    }
