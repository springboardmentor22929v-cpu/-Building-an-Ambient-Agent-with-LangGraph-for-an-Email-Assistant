from langgraph.graph import StateGraph, END
from src.agents.state import EmailAgentState
from src.nodes.triage import triage_node
from src.nodes.react_agent import react_agent_node

def create_email_agent():
    """
    Creates the email agent graph with triage and ReAct.
    """
    workflow = StateGraph(EmailAgentState)
    
    # Add nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("react_agent", react_agent_node)
    
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
            print("🤖 Action: Drafting response")
            return "react"  # Now we go to ReAct!
        
        return "end"
    
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "end": END,
            "react": "react_agent"
        }
    )
    
    # After ReAct, workflow ends
    workflow.add_edge("react_agent", END)
    
    # Compile
    app = workflow.compile()
    
    return app