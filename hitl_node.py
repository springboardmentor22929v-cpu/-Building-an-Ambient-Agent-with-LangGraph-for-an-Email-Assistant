# src/nodes/hitl_node.py

from typing import Literal
from state import AgentState


def hitl_checkpoint_node(state: AgentState) -> AgentState:
    """
    HITL checkpoint node.
    This does NOT ask for terminal input.
    It simply pauses the graph and waits for UI input.
    """

    print("🛑 HITL Checkpoint reached. Waiting for UI decision...")

    # If human decision not yet provided → pause here
    if not state.get("human_decision"):
        return {
            **state,
            "requires_approval": True
        }

    # If decision already exists (resume case)
    return state


def should_continue_after_hitl(state: AgentState) -> Literal["execute_node", "__end__"]:
    """
    Conditional router after HITL.
    """

    decision = state.get("human_decision")

    if decision in ["approve", "edit"]:
        print("✅ Human approved. Moving to execution.")
        return "execute_node"

    print("❌ Human denied. Ending workflow.")
    return "__end__"
