# graph.py
# Milestone 3: HITL with LangGraph Studio (Inbox-enabled)

from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from triage import triage_email, generate_email_draft
from m2_tools_langgraph import TOOLS
from m2_tools import DANGEROUS_TOOLS


# ==================================================
# 1️⃣ Define state
# ==================================================
class EmailState(TypedDict):
    # Structured Email Data
    sender: str
    subject: str
    body: str
    
    # Workflow State
    triage_decision: str
    planned_tool: Optional[str]
    human_decision: Optional[str]
    tool_result: Optional[str]
    # New fields for dynamic content
    generated_subject: Optional[str]
    generated_body: Optional[str]


# ==================================================
# 2️⃣ Triage node
# ==================================================
# ==================================================
# 2️⃣ Triage node (Dynamic Generation)
# ==================================================
def triage_node(state: EmailState) -> EmailState:
    print("🔥 TRIAGE NODE EXECUTED")
    
    # Construct text representation for LLM
    sender = state.get('sender', 'Unknown Sender')
    subject = state.get('subject', 'No Subject')
    body = state.get('body', 'No Body')
    
    email_text = f"From: {sender}\nSubject: {subject}\n\n{body}"
    
    decision = triage_email(email_text)
    
    planned_tool = None
    generated_subject = None
    generated_body = None
    
    if decision == "respond_act":
        # 🚨 DYNAMIC GENERATION: No more hardcoding!
        print("🧠 Generating response content with LLM...")
        content = generate_email_draft(email_text)
        generated_subject = content.get("subject")
        generated_body = content.get("body")
        planned_tool = "send_email"  # Logic change: Send directly (after approval)

    return {
        "sender": state["sender"],
        "subject": state["subject"],
        "body": state["body"],
        "triage_decision": decision,
        "planned_tool": planned_tool,
        "generated_subject": generated_subject,
        "generated_body": generated_body,
        "human_decision": None,
        "tool_result": None,
    }





# ==================================================
# 3️⃣ HITL checkpoint node (NO exception)
# ==================================================
# ==================================================
# 4️⃣ HITL checkpoint node (Wait for Approval)
# ==================================================
# ==================================================
# 3️⃣ HITL checkpoint node (Wait for Approval)
# ==================================================
def hitl_checkpoint_node(state: EmailState) -> EmailState:
    print("⏸️  WAITING FOR APPROVAL TO SEND")
    # This node does nothing but act as an interrupt point
    return state


# ==================================================
# 4️⃣ Human decision node
# ==================================================
# ==================================================
# 5️⃣ Human decision node
# ==================================================
def human_decision_node(state: EmailState) -> EmailState:
    decision = state.get("human_decision")
    print(f"🧑‍⚖️ HUMAN DECISION: {decision}")

    if not decision:
        print("⚠️  WARNING: Decision is NULL/None!")
        print("💡  TIP: In LangSmith Studio, you must EDIT the state to set 'human_decision': 'approve'")
        print("    If you just clicked 'Resume' without editing, it defaulted to None.")
        return {**state, "tool_result": "No decision made (Did you forget to edit state?)."}

    if decision == "deny":
        print("🚫 Action Denied.")
        return {**state, "tool_result": "Denied by human."}

    return state


# ==================================================
# 6️⃣ Send Node (Dangerous)
# ==================================================
# ==================================================
# 6️⃣ Tool Node (Send Email)
# ==================================================
def tool_node(state: EmailState) -> EmailState:
    print("🚀 TOOL NODE (SEND) EXECUTED")
    
    # In a real app, we might take the Draft ID via UI input,
    # but here we rely on the previously generated content for simulation,
    # or re-send cleanly.
    
    # Using 'send_email' tool
    # We send to the original sender
    recipient = state['sender']
    
    # Extract email if format is "Name <email>"
    if "<" in recipient and ">" in recipient:
        recipient = recipient.split("<")[1].split(">")[0]
    
    send_tool = next(t for t in TOOLS if t.name == "email_sender_tool")
    
    result = send_tool.invoke({
        "to": recipient,
        "subject": state["generated_subject"],
        "body": state["generated_body"]
    })
    
    return {**state, "tool_result": f"Email Sent: {result}"}





# ==================================================
# 6️⃣ Routing
# ==================================================
# ==================================================
# 7️⃣ Build graph
# ==================================================
builder = StateGraph(EmailState)

builder.add_node("triage", triage_node)
builder.add_node("hitl_checkpoint", hitl_checkpoint_node)
builder.add_node("human_decision", human_decision_node)
builder.add_node("tool_node", tool_node)

builder.set_entry_point("triage")

def route_after_triage(state: EmailState):
    if state["planned_tool"] == "send_email":
        return "hitl_checkpoint"
    return END

def route_after_human_decision(state: EmailState):
    decision = state.get("human_decision")
    print(f"🔄 ROUTING CHECK: Decision is '{decision}'")
    
    if decision == "approve":
        print("✅ Decision APPROVED -> Going to 'tool_node'")
        return "tool_node"
    
    print("🛑 Decision NOT APPROVED -> Going to END")
    return END

builder.add_conditional_edges("triage", route_after_triage)
builder.add_edge("hitl_checkpoint", "human_decision")
builder.add_conditional_edges("human_decision", route_after_human_decision)
builder.add_edge("tool_node", END)


# ==================================================
# 8️⃣ Compile with inbox interrupt
# ==================================================
# NOTE: When running with `langgraph dev`, it supplies its own checkpointer.
# We only need MemorySaver for local python script execution.
import os

if os.environ.get("LANGGRAPH_API_URL"):
    # We are likely running in langgraph dev/cloud
    checkpointer = None
else:
    # We are running locally via python script
    checkpointer = MemorySaver()

app = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_decision"]
)
