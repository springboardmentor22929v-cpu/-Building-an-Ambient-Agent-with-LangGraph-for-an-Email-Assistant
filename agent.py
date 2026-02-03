"""
Entry point for LangGraph Studio.
This file exposes the graph for the Studio interface.
"""

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from src.agents.state import EmailAgentState

from src.nodes.triage import triage_node
from src.nodes.react_agent import react_agent_node
from src.nodes.hitl import hitl_checkpoint_node, should_continue_after_hitl
from src.nodes.execute import execute_action_node

# Import and initialize Google services
from src.integrations.gmail_auth import authenticate_google_services
from src.tools.google_tools import initialize_tools


# Initialize services once when Studio loads
print("🔐 Initializing Google services...")
try:
    gmail, calendar = authenticate_google_services()
    initialize_tools(gmail, calendar)
    print("✅ Google services initialized")
except Exception as e:
    print(f"⚠️ Warning: Google services initialization failed: {e}")
    print("   Tools may not work until authentication succeeds")


def create_graph():
    """
    Create the email agent graph for LangGraph Studio.
    """

    workflow = StateGraph(EmailAgentState)

    # Add nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("react_agent", react_agent_node)
    workflow.add_node("hitl_checkpoint", hitl_checkpoint_node)
    workflow.add_node("execute_action", execute_action_node)

    # Entry point
    workflow.set_entry_point("triage")

    # Routing after triage
    def route_after_triage(state: EmailAgentState) -> str:
        decision = state["triage_decision"]

        if decision in ["ignore", "notify_human"]:
            return "end"
        elif decision == "respond":
            return "react"

        return "end"

    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "end": END,
            "react": "react_agent"
        }
    )

    # After ReAct → HITL checkpoint
    workflow.add_edge("react_agent", "hitl_checkpoint")

    # HITL routing
    workflow.add_conditional_edges(
        "hitl_checkpoint",
        should_continue_after_hitl,
        {
            "wait": END,        # Pause for human approval
            "execute": "execute_action",
            "end": END
        }
    )

    # After execution → End
    workflow.add_edge("execute_action", END)

    # ✅ Compile WITHOUT custom checkpointer
    compiled_graph = workflow.compile(
        interrupt_before=["hitl_checkpoint"]
    )

    return compiled_graph


# Graph instance for Studio
graph = create_graph()

print("✅ Email agent graph created and ready for LangGraph Studio")
