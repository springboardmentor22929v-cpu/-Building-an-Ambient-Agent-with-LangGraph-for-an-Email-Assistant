"""
Email Agent Graph
Studio-Compatible HITL Version
With Learning via Memory Nodes (no custom checkpointer needed - LangGraph provides built-in persistence)
"""

from langgraph.graph import StateGraph, END

from state import EmailAgentState
from email_triage import triage_node
from react_agent import react_agent_node
from hitl import hitl_checkpoint_node
from execute import execute_action_node
from memory import load_memory_node, update_memory_node


# Dangerous tools that require human approval
DANGEROUS_TOOLS = {
    "send_email",
    "create_calendar_invite",
    "schedule_meeting",
    "delete_email",
    "forward_email",
}


def create_email_agent():
    workflow = StateGraph(EmailAgentState)

    # ----------------------------------
    # ADD NODES
    # ----------------------------------
    workflow.add_node("load_memory", load_memory_node)  # Load context from memory
    workflow.add_node("triage", triage_node)
    workflow.add_node("react_agent", react_agent_node)
    workflow.add_node("hitl_checkpoint", hitl_checkpoint_node)
    workflow.add_node("execute_action", execute_action_node)
    workflow.add_node("save_memory", update_memory_node)  # Save to memory after execution

    # ----------------------------------
    # ENTRY POINT
    # ----------------------------------
    workflow.set_entry_point("load_memory")
    workflow.add_edge("load_memory", "triage")

    # ----------------------------------
    # TRIAGE ROUTING
    # ----------------------------------
    def route_after_triage(state: EmailAgentState):
        if state.get("triage_decision") == "respond":
            return "react"
        return "end"

    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "react": "react_agent",
            "end": END,
        },
    )

    # ----------------------------------
    # REACT ROUTING
    # ----------------------------------
    def route_after_react(state: EmailAgentState):
        pending_action = state.get("pending_action")

        if not pending_action:
            return "end"

        action_type = pending_action.get("action_type")

        if not action_type:
            return "end"

        if action_type in DANGEROUS_TOOLS:
            return "hitl"

        return "execute"

    workflow.add_conditional_edges(
        "react_agent",
        route_after_react,
        {
            "hitl": "hitl_checkpoint",
            "execute": "execute_action",
            "end": END,
        },
    )

    # ----------------------------------
    # HITL ROUTING
    # ----------------------------------
    def route_after_hitl(state: EmailAgentState):
        decision = state.get("hitl_decision")

        if decision == "approve":
            return "execute"

        if decision == "deny":
            return "end"

        if decision == "edit":
            return "execute"

        return "end"

    workflow.add_conditional_edges(
        "hitl_checkpoint",
        route_after_hitl,
        {
            "execute": "execute_action",
            "end": END,
        },
    )

    # ----------------------------------
    # MEMORY SAVING AFTER EXECUTION
    # ----------------------------------
    workflow.add_edge("execute_action", "save_memory")
    workflow.add_edge("save_memory", END)

    # ✅ COMPILE without custom checkpointer
    # LangGraph API provides built-in persistence automatically
    app = workflow.compile(
        interrupt_before=["hitl_checkpoint"],
    )

    return app


# Required for Studio to detect graph
app = create_email_agent()
