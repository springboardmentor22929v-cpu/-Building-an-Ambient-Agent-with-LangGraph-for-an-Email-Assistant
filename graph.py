# src/graph.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState

from nodes.load_memory_node import load_memory_node
from nodes.triage_node import triage_node
from nodes.react_node import react_node
from nodes.hitl_node import hitl_checkpoint_node, should_continue_after_hitl
from nodes.execute_node import execute_node
from nodes.update_memory_node import update_memory_node


def build_graph():
    workflow = StateGraph(AgentState)

    # -------------------------
    # Add Nodes
    # -------------------------
    workflow.add_node("load_memory", load_memory_node)
    workflow.add_node("triage", triage_node)
    workflow.add_node("react", react_node)
    workflow.add_node("hitl", hitl_checkpoint_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("update_memory", update_memory_node)

    # -------------------------
    # Entry Point
    # -------------------------
    workflow.set_entry_point("load_memory")

    # -------------------------
    # load_memory → triage
    # -------------------------
    workflow.add_edge("load_memory", "triage")

    # -------------------------
    # Triage Routing
    # -------------------------
    def route_after_triage(state: AgentState):
        decision = state.get("triage_decision")

        if decision in ["ignore", "notify_human"]:
            return "update_memory"

        if decision == "respond":
            return "react"

        # fallback
        return "update_memory"

    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "react": "react",
            "update_memory": "update_memory",
        },
    )

    # -------------------------
    # react → hitl
    # -------------------------
    workflow.add_edge("react", "hitl")

    # -------------------------
    # HITL Routing (Streamlit-based)
    # -------------------------
    workflow.add_conditional_edges(
        "hitl",
        should_continue_after_hitl,
        {
            "execute_node": "execute",   # approve or edit
            "__end__": END,              # deny
        },
    )

    # -------------------------
    # execute → update_memory
    # -------------------------
    workflow.add_edge("execute", "update_memory")

    # -------------------------
    # update_memory → END
    # -------------------------
    workflow.add_edge("update_memory", END)

    # -------------------------
    # Memory Checkpointer
    # -------------------------
    checkpointer = MemorySaver()

    app = workflow.compile(
        checkpointer=checkpointer
    )

    return app
