# app.py — Flask backend for Email Agent UI
import os
import sys
import json
import sqlite3
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from triage import triage_email, generate_email_draft
from m4_memory import init_memory, get_all_preferences, store_preference, log_processed_email, get_email_history, delete_processed_email
from m4_learning import learn_from_correction
from m4_tools import send_email

# Initialize memory DB
init_memory()

app = Flask(__name__)

# ──────────────────────────────────────────────
# In-memory state for current workflow
# ──────────────────────────────────────────────
workflow_state = {
    "steps": [],        # List of workflow step dicts
    "status": "idle",   # idle | processing | waiting_human | done
    "email": None,      # Current email being processed
    "triage_decision": None,
    "generated_subject": None,
    "generated_body": None,
    "initial_draft": None,
    "planned_tool": None,
}

def reset_state():
    workflow_state.update({
        "steps": [],
        "status": "idle",
        "email": None,
        "triage_decision": None,
        "generated_subject": None,
        "generated_body": None,
        "initial_draft": None,
        "planned_tool": None,
    })

def add_step(name, status, detail=""):
    workflow_state["steps"].append({
        "name": name,
        "status": status,
        "detail": detail
    })

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process_email():
    """Submit an email → run triage → return decision + draft if respond_act."""
    reset_state()
    data = request.json
    sender = data.get("sender", "")
    subject = data.get("subject", "")
    body = data.get("body", "")

    workflow_state["email"] = {"sender": sender, "subject": subject, "body": body}
    workflow_state["status"] = "processing"

    # Step 1: Load Memory
    add_step("load_memory", "completed", "Loading user preferences...")
    prefs = get_all_preferences()
    if prefs:
        pref_lines = [f"{k}: {v}" for k, v in prefs.items()]
        pref_detail = f"Found {len(prefs)} preference(s) — " + " | ".join(pref_lines)
    else:
        pref_detail = "No preferences found (blank slate)"
    workflow_state["steps"][-1]["detail"] = pref_detail

    # Step 2: Triage
    add_step("triage", "running", "Classifying email...")
    email_text = f"From: {sender}\nSubject: {subject}\n\n{body}"
    try:
        decision = triage_email(email_text)
    except Exception as e:
        workflow_state["steps"][-1]["status"] = "error"
        workflow_state["steps"][-1]["detail"] = str(e)
        workflow_state["status"] = "done"
        return jsonify({"error": str(e), "steps": workflow_state["steps"]}), 500

    workflow_state["triage_decision"] = decision
    workflow_state["steps"][-1]["status"] = "completed"
    workflow_state["steps"][-1]["detail"] = f"Decision: {decision}"

    # Step 3: Route based on decision
    if decision == "ignore":
        add_step("ignored", "completed", "Email classified as spam/irrelevant — ignored.")
        log_processed_email(sender, subject, body, "ignore", status="ignored", workflow_steps=json.dumps(workflow_state["steps"]))
        workflow_state["status"] = "done"
        return jsonify({
            "decision": decision,
            "steps": workflow_state["steps"],
            "status": "done"
        })

    elif decision == "notify_human":
        add_step("notify_human", "waiting", "Waiting for human: Ignore or Respond?")
        workflow_state["status"] = "waiting_human"
        return jsonify({
            "decision": decision,
            "steps": workflow_state["steps"],
            "status": "waiting_notify"
        })

    elif decision == "respond_act":
        # Generate draft
        add_step("generate_draft", "running", "Generating email draft...")
        try:
            draft = generate_email_draft(email_text, preferences=prefs)
            gen_body = draft.get("body", "")
            gen_subj = draft.get("subject", "")
        except Exception as e:
            workflow_state["steps"][-1]["status"] = "error"
            workflow_state["steps"][-1]["detail"] = str(e)
            workflow_state["status"] = "done"
            return jsonify({"error": str(e), "steps": workflow_state["steps"]}), 500

        workflow_state["generated_body"] = gen_body
        workflow_state["generated_subject"] = gen_subj
        workflow_state["initial_draft"] = gen_body
        workflow_state["planned_tool"] = "send_email"
        workflow_state["steps"][-1]["status"] = "completed"
        workflow_state["steps"][-1]["detail"] = "Draft generated successfully"

        add_step("hitl_checkpoint", "waiting", "Waiting for human: Approve, Edit, or Deny?")
        workflow_state["status"] = "waiting_human"

        return jsonify({
            "decision": decision,
            "generated_subject": gen_subj,
            "generated_body": gen_body,
            "steps": workflow_state["steps"],
            "status": "waiting_approve"
        })

    # Fallback
    return jsonify({"decision": decision, "steps": workflow_state["steps"]})


@app.route("/api/notify_decision", methods=["POST"])
def notify_decision():
    """Handle notify_human decision: ignore or respond."""
    data = request.json
    decision = data.get("decision", "").strip().lower()

    if decision == "ignore":
        add_step("notify_ignored", "completed", "Human chose to ignore this email.")
        email = workflow_state.get("email", {})
        if email:
            log_processed_email(email.get("sender"), email.get("subject"), email.get("body"), "notify_human", None, "ignored", workflow_steps=json.dumps(workflow_state["steps"]))
        workflow_state["status"] = "done"
        return jsonify({
            "result": "ignored",
            "steps": workflow_state["steps"],
            "status": "done"
        })

    elif decision == "respond":
        # Generate a draft
        add_step("generate_draft", "running", "Human chose to respond — generating draft...")
        email = workflow_state["email"]
        email_text = f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['body']}"
        prefs = get_all_preferences()

        try:
            draft = generate_email_draft(email_text, preferences=prefs)
            gen_body = draft.get("body", "")
            gen_subj = draft.get("subject", "")
        except Exception as e:
            workflow_state["steps"][-1]["status"] = "error"
            workflow_state["steps"][-1]["detail"] = str(e)
            return jsonify({"error": str(e), "steps": workflow_state["steps"]}), 500

        workflow_state["generated_body"] = gen_body
        workflow_state["generated_subject"] = gen_subj
        workflow_state["initial_draft"] = gen_body
        workflow_state["planned_tool"] = "send_email"
        workflow_state["steps"][-1]["status"] = "completed"
        workflow_state["steps"][-1]["detail"] = "Draft generated successfully"

        add_step("hitl_checkpoint", "waiting", "Waiting for human: Approve, Edit, or Deny?")
        workflow_state["status"] = "waiting_human"

        return jsonify({
            "decision": "respond",
            "generated_subject": gen_subj,
            "generated_body": gen_body,
            "steps": workflow_state["steps"],
            "status": "waiting_approve"
        })

    return jsonify({"error": "Invalid decision"}), 400


@app.route("/api/approve", methods=["POST"])
def approve_draft():
    """Approve the current draft and send via Gmail."""
    add_step("approved", "running", "Human approved — sending email...")

    email = workflow_state["email"]
    recipient = email["sender"]
    # Extract email address if format is "Name <email>"
    if "<" in recipient:
        recipient = recipient.split("<")[1].split(">")[0]

    try:
        result = send_email(
            to=recipient,
            subject=workflow_state["generated_subject"],
            body=workflow_state["generated_body"]
        )
        workflow_state["steps"][-1]["status"] = "completed"
        workflow_state["steps"][-1]["detail"] = result
        
        email = workflow_state.get("email", {})
        if email:
            log_processed_email(email.get("sender"), email.get("subject"), email.get("body"), workflow_state.get("triage_decision"), workflow_state.get("generated_body"), "sent", workflow_steps=json.dumps(workflow_state["steps"]))

        workflow_state["status"] = "done"
        return jsonify({
            "result": result,
            "steps": workflow_state["steps"],
            "status": "done"
        })
    except Exception as e:
        workflow_state["steps"][-1]["status"] = "error"
        workflow_state["steps"][-1]["detail"] = str(e)
        return jsonify({"error": str(e), "steps": workflow_state["steps"]}), 500


@app.route("/api/deny", methods=["POST"])
def deny_draft():
    """Deny the draft — discard without sending."""
    add_step("denied", "completed", "Human denied — email discarded.")
    
    email = workflow_state.get("email", {})
    if email:
        log_processed_email(email.get("sender"), email.get("subject"), email.get("body"), workflow_state.get("triage_decision"), workflow_state.get("generated_body"), "denied", workflow_steps=json.dumps(workflow_state["steps"]))

    workflow_state["status"] = "done"
    workflow_state["status"] = "done"
    return jsonify({
        "result": "Draft denied and discarded.",
        "steps": workflow_state["steps"],
        "status": "done"
    })


@app.route("/api/edit", methods=["POST"])
def edit_draft():
    """Submit edited draft → learn preference → send."""
    data = request.json
    edited_body = data.get("body", "")
    edited_subject = data.get("subject", workflow_state.get("generated_subject", ""))

    original_body = workflow_state.get("initial_draft", "")
    learned = None

    # Check if editing actually changed something
    if original_body and edited_body.strip() != original_body.strip():
        add_step("learning", "running", "Edit detected — learning preference...")
        try:
            learned = learn_from_correction(original_body, edited_body)
            if learned:
                workflow_state["steps"][-1]["detail"] = f"Learned: {learned}"
            else:
                workflow_state["steps"][-1]["detail"] = "No generalizable preference found"
            workflow_state["steps"][-1]["status"] = "completed"
        except Exception as e:
            workflow_state["steps"][-1]["status"] = "error"
            workflow_state["steps"][-1]["detail"] = str(e)

    # Update state with edited version
    workflow_state["generated_body"] = edited_body
    workflow_state["generated_subject"] = edited_subject

    # Send the edited email
    add_step("sending", "running", "Sending edited email...")
    email = workflow_state["email"]
    recipient = email["sender"]
    if "<" in recipient:
        recipient = recipient.split("<")[1].split(">")[0]

    try:
        result = send_email(to=recipient, subject=edited_subject, body=edited_body)
        workflow_state["steps"][-1]["status"] = "completed"
        workflow_state["steps"][-1]["detail"] = result
        
        email = workflow_state.get("email", {})
        if email:
            log_processed_email(email.get("sender"), email.get("subject"), email.get("body"), workflow_state.get("triage_decision", "respond_act"), edited_body, "sent", workflow_steps=json.dumps(workflow_state["steps"]))
            
        workflow_state["status"] = "done"
        return jsonify({
            "result": result,
            "learned": learned,
            "steps": workflow_state["steps"],
            "status": "done"
        })
    except Exception as e:
        workflow_state["steps"][-1]["status"] = "error"
        workflow_state["steps"][-1]["detail"] = str(e)
        return jsonify({"error": str(e), "steps": workflow_state["steps"]}), 500


@app.route("/api/preferences", methods=["GET"])
def get_preferences():
    """Get all stored preferences."""
    prefs = get_all_preferences()
    return jsonify({"preferences": prefs})


@app.route("/api/clear_memory", methods=["POST"])
def clear_memory():
    """Clear all preferences from SQLite."""
    import sqlite3
    try:
        conn = sqlite3.connect("agent_memory.sqlite")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_preferences")
        cursor.execute("DELETE FROM learning_history")
        conn.commit()
        conn.close()
        return jsonify({"result": "Memory cleared successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    """Get all email processing history."""
    history = get_email_history()
    return jsonify({"history": history})


@app.route("/api/history/delete/<int:email_id>", methods=["DELETE"])
def delete_history_item(email_id):
    """Delete a specific history entry."""
    deleted = delete_processed_email(email_id)
    if deleted:
        return jsonify({"result": "deleted"})
    return jsonify({"error": "Not found"}), 404


@app.route("/api/fetch_inbox", methods=["GET"])
def fetch_inbox():
    """Fetch latest emails from Gmail inbox."""
    try:
        from gmail_reader import get_latest_emails
        emails = get_latest_emails(max_results=5)
        # Track the latest message ID as "seen"
        if emails:
            app.config['LAST_SEEN_MSG_ID'] = emails[0].get('msg_id')
        return jsonify({"emails": emails})
    except Exception as e:
        return jsonify({"error": str(e), "emails": []}), 500


@app.route("/api/check_new", methods=["GET"])
def check_new():
    """Check for new emails since last check. Used for ambient monitoring."""
    try:
        from gmail_reader import get_latest_emails
        emails = get_latest_emails(max_results=1)
        
        if not emails:
            return jsonify({"has_new": False})
        
        latest = emails[0]
        last_seen = app.config.get('LAST_SEEN_MSG_ID')
        
        if last_seen is None:
            # First check — mark as seen, don't alert
            app.config['LAST_SEEN_MSG_ID'] = latest.get('msg_id')
            return jsonify({"has_new": False, "initialized": True})
        
        if latest.get('msg_id') != last_seen:
            # New email detected!
            app.config['LAST_SEEN_MSG_ID'] = latest.get('msg_id')
            return jsonify({
                "has_new": True,
                "email": {
                    "sender": latest.get("sender", "Unknown"),
                    "subject": latest.get("subject", "No subject"),
                    "body": latest.get("body", "")[:500]
                }
            })
        
        return jsonify({"has_new": False})
    except Exception as e:
        print(f"⚠️ Check new failed: {e}")
        return jsonify({"has_new": False, "error": str(e)})


if __name__ == "__main__":
    print("🚀 Email Agent UI starting at http://localhost:5000")
    app.run(debug=True, port=5000)
