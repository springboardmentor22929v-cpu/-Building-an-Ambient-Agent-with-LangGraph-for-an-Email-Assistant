from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.agents.state import EmailAgentState
from src.nodes.triage import triage_node
from src.nodes.react_agent import react_agent_node
from src.nodes.hitl import hitl_checkpoint_node, should_continue_after_hitl
from src.nodes.execute import execute_action_node


def create_email_agent():
    """
    Creates the email agent graph with HITL support.
    """
    workflow = StateGraph(EmailAgentState)
    
    # Add all nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("react_agent", react_agent_node)
    workflow.add_node("hitl_checkpoint", hitl_checkpoint_node)
    workflow.add_node("execute_action", execute_action_node)
    
    # Set entry point
    workflow.set_entry_point("triage")
    
    # Routing after triage
    def route_after_triage(state: EmailAgentState) -> str:
        decision = state["triage_decision"]
        
        if decision == "ignore":
            print("📦 Action: Archiving email")
            return "end"
        elif decision == "notify_human":
            print("🚨 Action: Notifying human")
            return "end"
        elif decision == "respond":
            print("🤖 Action: Processing with ReAct agent")
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
    
    # CRITICAL: After ReAct, ALWAYS go to HITL checkpoint
    # This was missing or incorrect before
    workflow.add_edge("react_agent", "hitl_checkpoint")
    
    # Routing after HITL
    workflow.add_conditional_edges(
        "hitl_checkpoint",
        should_continue_after_hitl,
        {
            "wait": END,           # Pause and wait for human input
            "execute": "execute_action",  # Human approved, execute
            "end": END             # Human denied, end workflow
        }
    )
    
    # After execution, end workflow
    workflow.add_edge("execute_action", END)
    
    # Compile with checkpointer (enables pause/resume)
    checkpointer = MemorySaver()
    
    # IMPORTANT: interrupt_before will pause BEFORE the node executes
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["hitl_checkpoint"]  # Pause before HITL
    )
    
    return app