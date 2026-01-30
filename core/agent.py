# core/agent.py

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from core.state import AgentState
from core.nodes import triage_node, draft_node, llm
from config.tool_loader import get_active_tools

# --- HITL CHANGE 1: Import MemorySaver ---
# We need memory to "save the game" when the agent pauses for human review.
from langgraph.checkpoint.memory import MemorySaver

# ==========================================
# 1. SETUP TOOLS
# ==========================================
# We ask the Tool Loader: "Are we in Real or Mock mode?"
tools = get_active_tools()

# We "bind" these tools to the LLM. 
llm_with_tools = llm.bind_tools(tools)

# ==========================================
# 2. BUILD THE GRAPH
# ==========================================
workflow = StateGraph(AgentState)

# -- Add the Nodes (The Steps) --
workflow.add_node("triage", triage_node)  # Step 1: Decide what to do
workflow.add_node("draft", draft_node)    # Step 2: Write the email (if needed)
workflow.add_node("action", ToolNode(tools)) # Step 3: Actually execute the tool (Send/Check Cal)

# -- Set the Entry Point --
workflow.set_entry_point("triage")

# ==========================================
# 3. DEFINE THE FLOW (The Routing)
# ==========================================

def route_triage(state):
    """
    This function acts as the Traffic Cop for the first step.
    """
    decision = state.get("triage_decision", "IGNORE")
    
    if decision == "RESPOND":
        return "draft"  # Go to the writing desk
    elif decision == "NOTIFY":
        return END      # Stop (In future, this could send a Slack alert)
    else:
        return END      # Stop (Ignore spam)

def should_continue(state):
    """
    Decides if the Agent needs to use a tool or is finished.
    """
    last_message = state["messages"][-1]
    
    # If the LLM just generated a tool call (like check_calendar or write_email),
    # we MUST go to the 'action' node to execute it.
    if last_message.tool_calls:
        return "action"
    
    # If no tool call, the agent is just talking/thinking. We stop.
    return END

# -- 1. Triage Logic --
workflow.add_conditional_edges(
    "triage", 
    route_triage,
    {
        "draft": "draft",
        END: END
    }
)

# -- 2. Draft Logic (The Smart Loop) --
# Instead of always going to action, we check: "Do you actually have a tool to run?"
workflow.add_conditional_edges(
    "draft",
    should_continue,
    {
        "action": "action",
        END: END
    }
)

# -- 3. Action Logic (The Return Trip) --
# CRITICAL FIX: After running a tool (like Calendar), go BACK to Draft.
# This allows the agent to read the calendar data and THEN write the email.
workflow.add_edge("action", "draft")

# ==========================================
# 4. COMPILE (HITL ENABLED)
# ==========================================

# Initialize the memory
memory = MemorySaver()

# --- HITL CHANGE 2: Compile with Interrupt ---
# We add `interrupt_before=["action"]`.
# This tells the agent: "PAUSE automatically right before you enter the 'action' node."
agent_engine = workflow.compile(
    checkpointer=memory,
    interrupt_before=["action"]
)