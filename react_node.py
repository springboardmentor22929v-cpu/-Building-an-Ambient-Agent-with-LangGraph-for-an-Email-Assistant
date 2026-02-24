from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState
from tools.safe_tools import read_calendar


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    convert_system_message_to_human=True
)


def react_node(state: AgentState) -> AgentState:
    print("\n🤖 REACT: Processing email")

    email_body = state["email_body"].lower()
    email_subject = state["email_subject"].lower()

    user_memory = state.get("user_preferences", {})
    sender_context = user_memory.get("sender_context", {})
    past_feedback = user_memory.get("past_feedback", [])
    preferences = user_memory.get("preferences", {})

    # =====================================
    # 1️⃣ Detect meeting intent
    # =====================================
    meeting_keywords = ["meet", "schedule", "call", "sync", "discussion"]
    is_meeting_request = any(
        keyword in email_body or keyword in email_subject
        for keyword in meeting_keywords
    )

    calendar_info = ""

    if is_meeting_request:
        calendar_info = read_calendar()
        print("   ✓ Calendar checked (safe tool)")

    calendar_section = ""
    if calendar_info:
        calendar_section = f"\nMy Calendar Availability:\n{calendar_info}\n"

    # =====================================
    # 2️⃣ Tone Adaptation from Memory
    # =====================================
    preferred_tone = "professional"

    if sender_context and sender_context.get("preferred_tone"):
        preferred_tone = sender_context["preferred_tone"]
        print(f"   🧠 Using preferred tone: {preferred_tone}")

    # If user edits often → enforce concise tone
    if past_feedback:
        print("   🧠 Adjusting tone due to past edits")
        preferred_tone = "concise"

    # =====================================
    # 3️⃣ Word Pattern Learning
    # =====================================
    avoid_words = preferences.get("avoid_words", "")
    prefer_words = preferences.get("prefer_words", "")

    pattern_instructions = ""
    if avoid_words:
        pattern_instructions += f"\nAvoid using these words: {avoid_words}."
    if prefer_words:
        pattern_instructions += f"\nPrefer using these words: {prefer_words}."

    # =====================================
    # 4️⃣ Build Adaptive Draft Prompt
    # =====================================
    draft_prompt = f"""
Draft a {preferred_tone} email reply.

Original Email:
Subject: {state['email_subject']}
Body: {state['email_body']}

{calendar_section}

Instructions:
- Tone: {preferred_tone}
- 2-3 short paragraphs
- Suggest meeting times if relevant
- End with 'Best regards'
- Only write email body (no subject or headers)
{pattern_instructions}

Write email body only:
"""

    try:
        draft_response = llm.invoke(draft_prompt)
        body_content = draft_response.content.strip()
        print("   ✓ Draft created")
    except Exception as e:
        body_content = "Thank you for your email. I will get back to you shortly."
        print(f"   ✗ Draft error: {e}")

    # =====================================
    # 5️⃣ Format Subject
    # =====================================
    subject = (
        f"Re: {state['email_subject']}"
        if not state["email_subject"].startswith("Re:")
        else state["email_subject"]
    )

    # =====================================
    # 6️⃣ Format Preview
    # =====================================
    formatted_preview = f"""To: {state.get("email_from", "sender@example.com")}
Subject: {subject}

{body_content}
"""

    # =====================================
    # 7️⃣ Dangerous Action (HITL Required)
    # =====================================
    pending_action = {
        "action_type": "send_email",
        "args": {
            "recipient": state.get("email_from", "sender@example.com"),
            "subject": subject,
            "body": body_content,
            "draft_preview": formatted_preview
        }
    }

    print("   📤 Action queued: send_email (requires approval)")

    return {
        **state,
        "pending_action": pending_action
    }
