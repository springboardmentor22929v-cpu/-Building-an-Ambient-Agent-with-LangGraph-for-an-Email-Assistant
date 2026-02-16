"""
main.py — CLI runner for the Ambient Email Assistant Agent.

Fetches REAL emails from Gmail via the API, runs them through the
LangGraph pipeline, and provides a terminal-based Human-in-the-Loop
(HITL) approval flow.

Usage:
    python main.py                  # Process 5 most recent unread emails
    python main.py --limit 10       # Process 10 emails
    python main.py --query "is:unread from:boss@company.com"
    python main.py --all            # Process all recent (read + unread)
"""

import sys
import argparse

from dotenv import load_dotenv
load_dotenv()

# ── Google auth + tool initialisation ───────────────────────────────
from src.integrations.gmail_auth import authenticate_google_services
from src.integrations.gmail_fetch import get_recent_emails
from src.tools.google_tools import initialize_tools

print("🔐 Authenticating with Google services...")
try:
    gmail, calendar, tasks = authenticate_google_services()
    initialize_tools(gmail, calendar, tasks)
    print("✅ Google services ready.\n")
except Exception as e:
    print(f"❌ Google authentication failed: {e}")
    print("   Make sure credentials.json exists and run setup_auth.ipynb first.")
    sys.exit(1)

# ── LangGraph imports ───────────────────────────────────────────────
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.agents.state import EmailAgentState
from src.nodes.triage import triage_node
from src.nodes.react_agent import react_agent_node
from src.nodes.hitl import hitl_checkpoint_node, should_continue_after_hitl
from src.nodes.execute import execute_action_node


def build_graph():
    """Build and compile the email agent graph with a MemorySaver checkpointer."""
    workflow = StateGraph(EmailAgentState)

    workflow.add_node("triage", triage_node)
    workflow.add_node("react_agent", react_agent_node)
    workflow.add_node("hitl_checkpoint", hitl_checkpoint_node)
    workflow.add_node("execute_action", execute_action_node)

    workflow.set_entry_point("triage")

    def route_after_triage(state: EmailAgentState) -> str:
        decision = state.get("triage_decision", "")
        if decision in ("ignore", "notify_human"):
            return "end"
        elif decision == "respond":
            return "react"
        return "end"

    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {"end": END, "react": "react_agent"},
    )

    workflow.add_edge("react_agent", "hitl_checkpoint")

    workflow.add_conditional_edges(
        "hitl_checkpoint",
        should_continue_after_hitl,
        {"wait": END, "execute": "execute_action", "end": END},
    )

    workflow.add_edge("execute_action", END)

    checkpointer = MemorySaver()
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["hitl_checkpoint"],
    )


# ── Fetch real emails from Gmail ────────────────────────────────────

def fetch_live_emails(max_results: int = 5, query: str = "is:unread"):
    """
    Pull real emails from Gmail API and convert them into the format
    expected by the LangGraph pipeline.
    """
    print(f"📬 Fetching up to {max_results} emails from Gmail...")
    print(f"   Query: {query}\n")

    raw_emails = get_recent_emails(gmail, max_results=max_results, query=query)

    if not raw_emails:
        print("📭 No emails found matching your query.")
        return []

    # Convert gmail_fetch format → pipeline format
    emails = []
    for e in raw_emails:
        if e is None:
            continue
        emails.append({
            "id": e.get("id", "unknown"),
            "from": e.get("from", e.get("from_full", "")),
            "to": "me",
            "subject": e.get("subject", "(no subject)"),
            "body": e.get("body", e.get("snippet", "")),
        })

    print(f"✅ Fetched {len(emails)} emails.\n")
    return emails


# ── HITL terminal prompt ────────────────────────────────────────────

def hitl_prompt(state: dict) -> dict:
    """
    Display the pending action and ask the user to APPROVE / DENY / EDIT.
    """
    pending = state.get("pending_action")
    if not pending:
        return {"human_decision": "approve", "requires_approval": False}

    args = pending.get("args", {})
    print("\n" + "=" * 70)
    print("🛑  HUMAN-IN-THE-LOOP — Approval Required")
    print("=" * 70)
    print(f"  Action : {pending.get('action_type')}")
    print(f"  To     : {args.get('recipient', 'N/A')}")
    print(f"  Subject: {args.get('subject', 'N/A')}")
    print("-" * 70)
    print(args.get("draft_preview", args.get("body", "")))
    print("-" * 70)
    print()
    print("  Type one of:")
    print("    APPROVE         — send as-is")
    print("    DENY            — cancel this action")
    print("    EDIT <new body> — replace body text and send")
    print()

    while True:
        choice = input("Your decision ▸ ").strip()
        if not choice:
            continue

        upper = choice.upper()
        if upper == "APPROVE":
            return {"human_decision": "approve"}
        elif upper == "DENY":
            return {"human_decision": "deny"}
        elif upper.startswith("EDIT"):
            new_body = choice[4:].strip()
            if not new_body:
                new_body = input("Enter new email body:\n▸ ").strip()
            return {
                "human_decision": "edit",
                "human_feedback": {"body": new_body, "draft_preview": new_body},
            }
        else:
            print("  ⚠ Please type APPROVE, DENY, or EDIT <text>.")


# ── Process a single email ──────────────────────────────────────────

def process_email(app, email_data: dict, thread_id: str):
    """Run a single email through the full pipeline with HITL."""

    initial_state = {
        "email_id": email_data.get("id", "unknown"),
        "email_from": email_data.get("from", ""),
        "email_to": email_data.get("to", "me"),
        "email_subject": email_data.get("subject", ""),
        "email_body": email_data.get("body", ""),
        "triage_decision": "",
        "triage_reasoning": "",
        "messages": [],
        "pending_action": None,
        "requires_approval": False,
        "human_decision": None,
        "human_feedback": None,
        "user_preferences": {},
    }

    config = {"configurable": {"thread_id": thread_id}}

    # 1️⃣  First run — triage → react_agent → (pauses before hitl_checkpoint)
    print(f"\n{'━' * 70}")
    print(f"📨 Processing: {initial_state['email_subject']}")
    print(f"   From: {initial_state['email_from']}")
    print(f"{'━' * 70}")

    result = None
    for event in app.stream(initial_state, config):
        for node_name, node_state in event.items():
            result = node_state

    if result is None:
        result = app.get_state(config).values

    # Check triage decision
    triage = result.get("triage_decision", "")
    print(f"\n   📋 Triage decision: {triage.upper()}")
    print(f"   📝 Reason: {result.get('triage_reasoning', 'N/A')}")

    if triage != "respond":
        print(f"   → No action needed. Moving on.\n")
        return

    # 2️⃣  Graph paused before hitl_checkpoint — get human input
    snapshot = app.get_state(config)
    current_state = snapshot.values

    if current_state.get("pending_action"):
        updates = hitl_prompt(current_state)
        app.update_state(config, updates)

        # 3️⃣  Continue execution
        for event in app.stream(None, config):
            for node_name, node_state in event.items():
                result = node_state

        final_state = app.get_state(config).values

        decision = final_state.get("human_decision", "")
        if decision in ("approve", "edit"):
            status = final_state.get("execution_status", "unknown")
            if status == "success":
                print("\n✅ Action executed successfully!")
            else:
                print(f"\n⚠️  Execution status: {status}")
        elif decision == "deny":
            print("\n🚫 Action cancelled by human.")
    else:
        print("   ℹ️  No dangerous action pending — auto-completed.\n")


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ambient Email Assistant Agent")
    parser.add_argument("--limit", type=int, default=5,
                        help="Number of emails to fetch (default: 5)")
    parser.add_argument("--query", type=str, default="is:unread",
                        help='Gmail search query (default: "is:unread")')
    parser.add_argument("--all", action="store_true",
                        help="Fetch all recent emails (not just unread)")
    args = parser.parse_args()

    query = "" if args.all else args.query

    # Fetch REAL emails from Gmail
    emails = fetch_live_emails(max_results=args.limit, query=query)

    if not emails:
        print("Nothing to process. Exiting.")
        sys.exit(0)

    # Build graph
    app = build_graph()
    print("✅ LangGraph agent compiled.\n")

    # Process each email
    for idx, email_data in enumerate(emails):
        thread_id = f"email-{email_data.get('id', idx)}"
        process_email(app, email_data, thread_id)

    print("\n" + "=" * 70)
    print("✅ All emails processed. Goodbye!")
    print("=" * 70)


if __name__ == "__main__":
    main()
