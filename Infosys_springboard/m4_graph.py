# m4_graph.py
import sqlite3
import json
from typing import TypedDict, Optional, Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# M4 Modules
from m4_memory import get_all_preferences, init_memory
from m4_learning import learn_from_correction
from m4_tools import (
    check_calendar_availability,
    schedule_meeting,
    draft_email_reply,
    send_email,
    DANGEROUS_TOOLS
)
# Reuse triage logic (updated for M4)
from triage import triage_email, generate_email_draft

# Ensure DB is ready
init_memory()

# ==================================================
# 1️⃣ Define State
# ==================================================
class EmailState(TypedDict):
    sender: str
    subject: str
    body: str
    
    triage_decision: str
    # Memory
    user_preferences: Dict[str, str]
    
    # Draft tracking for Learning
    initial_draft: Optional[str]      # What AI wrote (set at triage)
    pre_edit_draft: Optional[str]     # Snapshot saved at HITL checkpoint (before user can Fork)
    generated_subject: Optional[str]
    generated_body: Optional[str]     # What Human sends (can be edited via Fork)
    
    planned_tool: Optional[str]
    human_decision: Optional[str]          # approve / deny for respond_act flow
    notify_human_decision: Optional[str]   # ignore / respond for notify_human flow
    tool_result: Optional[str]

# ==================================================
# 2️⃣ Nodes
# ==================================================

def load_memory_node(state: EmailState) -> EmailState:
    """Fetch user preferences from SQLite."""
    print("🧠 Loading user memory...")
    prefs = get_all_preferences()
    if prefs:
        print(f"   Found preferences: {prefs}")
    else:
        print("   No preferences found (Blank slate).")
        
    return {"user_preferences": prefs}

def triage_node(state: EmailState) -> EmailState:
    print("🔥 TRIAGE NODE (M4 - Memory Aware)")
    
    email_text = f"From: {state['sender']}\nSubject: {state['subject']}\n\n{state['body']}"
    
    # 1. Decide
    decision = triage_email(email_text)
    
    planned_tool = None
    gen_subj = None
    gen_body = None
    initial_draft_text = None
    
    # 2. Act (Drafting with Preference Injection)
    if decision == "respond_act":
        print("   Drafting response using Memory...")
        prefs = state.get("user_preferences", {})
        
        # Pass prefs to updated generate function
        draft = generate_email_draft(email_text, preferences=prefs)
        
        gen_subj = draft.get("subject")
        gen_body = draft.get("body")
        initial_draft_text = gen_body # Save original for comparison later
        
        planned_tool = "send_email"

    return {
        "triage_decision": decision,
        "planned_tool": planned_tool,
        "generated_subject": gen_subj,
        "generated_body": gen_body,
        "initial_draft": initial_draft_text
    }

def notify_human_checkpoint_node(state: EmailState) -> EmailState:
    """Pause point for notify_human emails — human sees the email and decides.
    Human sets notify_human_decision = 'ignore' or 'respond'.
    """
    print("🔔 NOTIFY HUMAN CHECKPOINT")
    print(f"   From: {state.get('sender')}")
    print(f"   Subject: {state.get('subject')}")
    print(f"   Body preview: {state.get('body', '')[:120]}")
    print("   ⏳ Set notify_human_decision = 'ignore' or 'respond'")
    return state


def generate_draft_node(state: EmailState) -> EmailState:
    """Generates a reply draft when human chose 'respond' at notify_human_checkpoint.
    This runs as a proper graph node so Studio doesn't skip it.
    """
    print("✍️  GENERATING DRAFT for notify_human → respond flow")
    email_text = f"From: {state.get('sender')}\nSubject: {state.get('subject')}\n\n{state.get('body', '')}"
    prefs = state.get("user_preferences", {})
    draft = generate_email_draft(email_text, preferences=prefs)
    gen_body = draft.get("body")
    gen_subj = draft.get("subject")
    print(f"   ✅ Draft ready: {gen_body[:80] if gen_body else 'None'}...")
    return {
        **state,
        "generated_body": gen_body,
        "generated_subject": gen_subj,
        "initial_draft": gen_body,
        "planned_tool": "send_email"
    }




def hitl_checkpoint_node(state: EmailState) -> EmailState:
    print("⏸️  WAITING FOR HUMAN INPUT (Approve/Edit/Deny)")
    # Note: initial_draft was set by triage_node with the original AI draft.
    # The user will Fork from triage node, editing only generated_body.
    # initial_draft stays as the original since user doesn't change it.
    return state

def human_decision_node(state: EmailState) -> EmailState:
    decision = state.get("human_decision")
    print(f"🧑‍⚖️ HUMAN DECISION: {decision}")
    
    # Check for Learning Opportunity (Implicit "Edit")
    # If the current 'generated_body' is different from 'initial_draft',
    # it means the human EDITED the state in the Studio before clicking Approve.
    
    current_body = state.get("generated_body")
    # initial_draft is set by triage_node (original AI draft).
    # When user forks from triage node, they only edit generated_body,
    # leaving initial_draft as the original value. This is correct for comparison.
    original_body = state.get("initial_draft")
    
    print(f"🔍 DEBUG - initial_draft (first 80): {repr(original_body[:80]) if original_body else 'NONE'}")
    print(f"🔍 DEBUG - generated_body (first 80): {repr(current_body[:80]) if current_body else 'NONE'}")
    # Compare full strings
    if original_body and current_body:
        print(f"🔍 MATCH: {original_body.strip() == current_body.strip()}")
    
    if decision == "approve" and current_body and original_body:
        if current_body.strip() != original_body.strip():
            print("🎓 EDIT DETECTED! Triggering Learning...")
            learn_from_correction(original_body, current_body)
        else:
            print("ℹ️  No edit detected — drafts are identical.")
            
    if decision == "deny":
        return {**state, "tool_result": "Denied by human."}
        
    return state

def tool_node(state: EmailState) -> EmailState:
    tool_name = state.get("planned_tool")
    print(f"🛠️ TOOL NODE: Executing {tool_name}")
    
    result = "No action taken"
    
    # ✅ Learning check here too — catches Studio "Fork" flow
    # When user uses Fork in Studio, human_decision_node is bypassed.
    # So we also check for edits here, right before sending.
    current_body = state.get("generated_body")
    original_body = state.get("initial_draft")
    print(f"🔍 DEBUG (tool_node) - initial_draft (first 80): {repr(original_body[:80]) if original_body else 'NONE'}")
    print(f"🔍 DEBUG (tool_node) - generated_body (first 80): {repr(current_body[:80]) if current_body else 'NONE'}")
    if original_body and current_body:
        print(f"🔍 MATCH in tool_node: {original_body.strip() == current_body.strip()}")
    if current_body and original_body and current_body.strip() != original_body.strip():
        print("🎓 EDIT DETECTED (via Fork)! Triggering Learning...")
        learn_from_correction(original_body, current_body)
    elif current_body and original_body:
        print("ℹ️  No edit detected in tool_node — drafts are identical.")

    
    # Simple tool routing
    if tool_name == "send_email":
        # Extract Recipient (from sender)
        recipient = state['sender']
        if "<" in recipient:
            recipient = recipient.split("<")[1].split(">")[0]
            
        result = send_email(
            to=recipient,
            subject=state.get("generated_subject"),
            body=state.get("generated_body")
        )
        
    return {**state, "tool_result": result}

# ==================================================
# 3️⃣ Graph Definition
# ==================================================

builder = StateGraph(EmailState)

builder.add_node("load_memory", load_memory_node)
builder.add_node("triage", triage_node)
builder.add_node("notify_human_checkpoint", notify_human_checkpoint_node)
builder.add_node("generate_draft", generate_draft_node)
builder.add_node("hitl_checkpoint", hitl_checkpoint_node)
builder.add_node("human_decision", human_decision_node)
builder.add_node("tool_node", tool_node)

builder.set_entry_point("load_memory")

builder.add_edge("load_memory", "triage")

def route_after_triage(state: EmailState):
    decision = state.get("triage_decision")
    if decision == "respond_act":
        return "hitl_checkpoint"
    elif decision == "notify_human":
        return "notify_human_checkpoint"
    return END  # ignore

def route_after_notify_human(state: EmailState):
    """Route based on human's choice: ignore or respond."""
    notify_decision = state.get("notify_human_decision", "").strip().lower()
    print(f"🔄 NOTIFY ROUTING: '{notify_decision}'")
    if notify_decision == "respond":
        return "generate_draft"  # Generate draft first, then HITL flow
    print("🗑️  Email ignored by human.")
    return END

def route_after_human(state: EmailState):
    if state.get("human_decision") == "approve":
        return "tool_node"
    return END

builder.add_conditional_edges("triage", route_after_triage)
builder.add_conditional_edges("notify_human_checkpoint", route_after_notify_human)
builder.add_edge("generate_draft", "hitl_checkpoint")  # Draft → HITL approval
builder.add_edge("hitl_checkpoint", "human_decision")
builder.add_conditional_edges("human_decision", route_after_human)
builder.add_edge("tool_node", END)

# When running in Studio, checkpointer is injected automatically.
# We modify this line to compile WITHOUT a hardcoded checkpointer.
# For evaluation (m4_evaluation.py), we will explicitly pass one.

app = builder.compile(
    interrupt_before=["notify_human_checkpoint", "human_decision"]
)

