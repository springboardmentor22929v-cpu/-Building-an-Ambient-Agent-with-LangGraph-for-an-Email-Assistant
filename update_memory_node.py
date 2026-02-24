from state import AgentState
from memory.AgentMemory import AgentMemory
from datetime import datetime
import uuid


def update_memory_node(state: AgentState) -> AgentState:
    print("\n💾 Updating Memory")

    memory = AgentMemory()

    email_id = state.get("email_id") or str(uuid.uuid4())
    email_from = state.get("email_from")
    email_subject = state.get("email_subject")
    triage_decision = state.get("triage_decision")
    human_decision = state.get("human_decision")

    # ===== 1️⃣ Save Email Interaction =====
    action_taken = (
        state.get("pending_action", {}).get("action_type")
        if state.get("pending_action")
        else "none"
    )

    memory.save_email_interaction(
        email_id=email_id,
        email_from=email_from,
        email_subject=email_subject,
        triage_decision=triage_decision,
        action_taken=action_taken,
        human_approved=(human_decision == "approve")
    )

    # ===== 2️⃣ Save Feedback if Edited =====
    if human_decision == "edit":
        original_draft = state.get("pending_action", {}).get("args", {}).get("draft_preview", "")
        edited_draft = state.get("execution_result", "")

        memory.save_feedback(
            email_id=email_id,
            email_from=email_from,
            email_subject=email_subject,
            original_draft=original_draft,
            edited_draft=edited_draft,
            feedback_note="User edited draft",
            action="edit"
        )

    # ===== 3️⃣ Save Triage Correction if Denied =====
    if human_decision == "deny":
        memory.save_triage_correction(
            email_from=email_from,
            email_subject=email_subject,
            original_decision=triage_decision,
            corrected_decision="notify_human",
            reason="Human denied auto-response"
        )

    # ===== 4️⃣ Update Sender Context Interaction Count =====
    memory.save_sender_context(
        sender_email=email_from
    )

    print("   ✓ Memory updated successfully")

    return {
        **state,
        "memory_saved": True
    }
