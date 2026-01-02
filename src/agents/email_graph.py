from langgraph.graph import StateGraph, END
from src.agents.state import EmailAgentState
from src.nodes.triage import triage_node

def create_email_agent():
    """
    Creates the email agent graph with triage functionality.
    """
    # Initialize graph
    workflow = StateGraph(EmailAgentState)
    
    # Add triage node
    workflow.add_node("triage", triage_node)
    
    # Set entry point
    workflow.set_entry_point("triage")
    
    # Add conditional routing based on triage decision
    def route_after_triage(state: EmailAgentState) -> str:
        decision = state["triage_decision"]
        
        if decision == "ignore":
            print("📦 Action: Archiving email")
            return "end"
        elif decision == "notify_human":
            print("🚨 Action: Notifying human")
            return "end"
        elif decision == "respond":
            print("🤖 Action: Will draft response")
            return "end"  # For now, just end (we'll add ReAct later)
        
        return "end"
    
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "end": END
        }
    )
    
    # Compile
    app = workflow.compile()
    
    return app