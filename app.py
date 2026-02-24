# src/app.py

import streamlit as st
import json
from copy import deepcopy
from uuid import uuid4
import sys
import os

# Fix import path so src modules work properly
sys.path.append(os.path.dirname(__file__))

from graph import build_graph


# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Ambient Email Agent",
    page_icon="📧",
    layout="wide"
)

# ===============================
# SESSION INITIALIZATION
# ===============================
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"streamlit-thread-{uuid4().hex[:8]}"

if "agent_state" not in st.session_state:
    st.session_state.agent_state = None


# ===============================
# SIDEBAR
# ===============================
st.sidebar.title("⚙️ Controls")
st.sidebar.write(f"**Thread ID:** `{st.session_state.thread_id}`")

if st.sidebar.button("🔄 Reset Session"):
    st.session_state.agent_state = None
    st.rerun()



# ===============================
# HEADER
# ===============================
st.title("📧 Ambient Email Agent")
st.caption("AI-powered Email Assistant with Memory + HITL (Human-in-the-loop)")


# ===============================
# HELPER: SAFE GRAPH INVOCATION
# ===============================
def invoke_graph(state):
    try:
        with st.spinner("🤖 Agent is thinking..."):
            result = st.session_state.graph.invoke(
                state,
                config={"configurable": {"thread_id": st.session_state.thread_id}}
            )
        return result, None
    except Exception as e:
        return None, e


# ===============================
# EMAIL COMPOSE SECTION
# ===============================
with st.container():
    st.subheader("✉️ Compose Email")

    with st.form("email_form"):
        col1, col2 = st.columns(2)

        with col1:
            email_subject = st.text_input("Email Subject")

        with col2:
            email_from = st.text_input("From", value="sender@example.com")

        email_body = st.text_area("Email Body", height=180)

        submitted = st.form_submit_button("🚀 Run Agent")

# ===============================
# RUN AGENT
# ===============================
if submitted:

    initial_state = {
        "email_id": None,
        "email_from": email_from,
        "email_subject": email_subject,
        "email_body": email_body,
        "triage_decision": None,
        "triage_reasoning": None,
        "messages": None,
        "pending_action": None,
        "requires_approval": False,
        "human_decision": None,
        "human_feedback": None,
        "execution_result": None,
        "execution_status": None,
        "user_preferences": {},
        "memory_saved": False,
        "workflow_id": None,
    }

    result, err = invoke_graph(initial_state)

    if err:
        st.error(f"❌ Agent Error: {err}")
    else:
        st.session_state.agent_state = result


# ===============================
# DISPLAY RESULTS
# ===============================
state = st.session_state.agent_state

if state is None:
    st.info("Run the agent by entering email details and clicking **Run Agent**.")
else:

    st.divider()

    # ---------------------------
    # TRIAGE RESULT
    # ---------------------------
    st.subheader("🧠 Triage Result")

    decision = state.get("triage_decision")
    reasoning = state.get("triage_reasoning")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Decision", decision.upper() if decision else "N/A")

    with col2:
        st.write("**Reasoning:**")
        st.write(reasoning)

    # ---------------------------
    # MEMORY DISPLAY
    # ---------------------------
    memory = state.get("user_preferences")
    if memory:
        with st.expander("🗂 Memory Context"):
            st.json(memory)

    # ---------------------------
    # HITL SECTION
    # ---------------------------
    pending = state.get("pending_action")

    if pending:

        st.divider()
        st.subheader("📤 Human Review Required")

        draft_preview = pending.get("args", {}).get("draft_preview", "")

        edited_draft = st.text_area(
            "✏️ Edit Draft Before Sending",
            value=draft_preview,
            height=250
        )

        col1, col2, col3 = st.columns(3)

        # APPROVE
        if col1.button("✅ Approve"):
            next_state = deepcopy(state)
            next_state["human_decision"] = "approve"

            result, err = invoke_graph(next_state)

            if err:
                st.error(f"Resume Error: {err}")
            else:
                st.success("✅ Email Approved & Sent")
                st.session_state.agent_state = result
                st.rerun()


        # EDIT & SEND
        if col2.button("✏️ Edit & Send"):
            next_state = deepcopy(state)
            next_state["human_decision"] = "edit"
            next_state["human_feedback"] = {
                "body_content": edited_draft
            }

            result, err = invoke_graph(next_state)

            if err:
                st.error(f"Resume Error: {err}")
            else:
                st.success("✏️ Edited Email Sent")
                st.session_state.agent_state = result
                st.rerun()


        # DENY
        if col3.button("❌ Deny"):
            next_state = deepcopy(state)
            next_state["human_decision"] = "deny"

            result, err = invoke_graph(next_state)

            if err:
                st.error(f"Resume Error: {err}")
            else:
                st.warning("❌ Email Sending Cancelled")
                st.session_state.agent_state = result
                st.rerun()


    else:
        st.success("✔ No pending dangerous action.")

    # ---------------------------
    # EXECUTION RESULT
    # ---------------------------
    if state.get("execution_result"):
        st.divider()
        st.subheader("📨 Execution Result")
        st.success(state.get("execution_result"))

    # ---------------------------
    # DEBUG STATE
    # ---------------------------
    with st.expander("🔍 Full Agent State (Debug)"):
        try:
            st.json(state)
        except Exception:
            st.text(json.dumps(state, default=str, indent=2))
