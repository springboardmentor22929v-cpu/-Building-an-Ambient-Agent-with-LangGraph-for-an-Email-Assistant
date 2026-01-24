# core/agent.py

# ==========================================
# 1. IMPORTS
# ==========================================
import datetime
from typing import TypedDict, Annotated, List, Literal
import operator

# Import LangChain logic for messages
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.tools import tool

# Import LangGraph to build the workflow (Nodes and Edges)
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

# Import our custom modules we built earlier
from core.llm import get_llm    # To get the AI model (Groq/Gemini)
from tools.base import get_tools # To get the correct tools (Real/Mock)

# ==========================================
# 2. DEFINE THE STATE (Memory)
# ==========================================
# This acts as the "Short-term Memory" of the agent.
# It keeps track of the email content and the AI's decision.
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add] # Stores the conversation history
    email_category: str  # Stores if it is 'ignore', 'respond', or 'notify'

# ==========================================
# 3. SETUP THE TRIAGE (Classifier)
# ==========================================
# This defines the structure of the output we want from the AI.
# We force the AI to give us a 'category' and 'reasoning'.
class TriageDecision(BaseModel):
    category: str = Field(description="The category: 'ignore', 'notify_human', or 'respond'")
    reasoning: str = Field(description="Why this category was chosen.")

# Get the LLM (Groq or Gemini)
triage_model = get_llm(temperature=0) 

# Force the LLM to output Structured Data (JSON)
triage_llm = triage_model.with_structured_output(TriageDecision)

def triage_node(state: AgentState):
    """
    NODE 1: TRIAGE
    This function looks at the email and decides what to do with it.
    """
    # Get the email content from the state
    email_content = state["messages"][-1].content
    print(f"\n🧐 [TRIAGE] Analyzing email...")

    # Ask the AI to classify the email
    decision = triage_llm.invoke(f"""
    Analyze this email and classify it into exactly one category:
    
    1. 'ignore': Spam, promotions, or useless info.
    2. 'notify_human': Urgent issues that need a human to look at (but no auto-reply).
    3. 'respond': Routine questions or scheduling requests where I can help.

    Email Content:
    {email_content}
    """)
    
    print(f"   -> Decision: {decision.category.upper()} ({decision.reasoning})")
    
    # Save the decision to the state
    return {"email_category": decision.category}

# ==========================================
# 4. SETUP THE ACTION (Worker)
# ==========================================
# This is the "Worker" that uses tools.

# Get the tools (Real or Mock based on your .env)
tools_list = get_tools()

# Get the LLM for the worker
worker_model = get_llm(temperature=0)

# Create the ReAct Agent
# This is a pre-built agent that knows how to think and use tools loop
agent_worker = create_react_agent(worker_model, tools_list)

def action_node(state: AgentState):
    """
    NODE 2: ACTION
    This function runs only if the email category is 'respond'.
    It uses tools to draft a reply.
    """
    print("🤖 [AGENT] Working on response...")
    
    # Get today's date for context
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # Create a System Prompt to guide the agent
    sys_msg = SystemMessage(content=f"""
    You are a helpful office assistant. Today is {today}.
    
    YOUR GOAL: Draft a helpful email reply.
    
    INSTRUCTIONS:
    1. If the user asks about a specific project or date, use your TOOLS to check.
    2. Do NOT guess. If you need info, use the tool.
    3. Once you have the info, draft a polite response.
    """)
    
    # Combine System Prompt + Email History
    input_messages = [sys_msg] + state["messages"]
    
    # Run the Agent (Thinking -> Tool -> Thinking -> Response)
    result = agent_worker.invoke({"messages": input_messages})
    
    # Return the final message (the drafted email)
    return {"messages": [result["messages"][-1]]}

# ==========================================
# 5. BUILD THE GRAPH (Workflow)
# ==========================================
# This connects the nodes together into a flow chart.

workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("triage", triage_node)
workflow.add_node("action", action_node)

# Set the starting point
workflow.set_entry_point("triage")

# Define the Logic (Conditional Edges)
def route_email(state: AgentState):
    """
    This function acts as a traffic cop.
    It looks at the category and points to the next step.
    """
    if state["email_category"] == "respond":
        return "action" # Go to the worker
    else:
        return END      # Stop (Ignore or Notify)

# Add the edges
workflow.add_conditional_edges("triage", route_email)
workflow.add_edge("action", END)

# Compile the graph into a runnable app
app = workflow.compile()