"""
ReAct Agent Node
Processes email and prepares an action for HITL approval.
"""

from datetime import datetime, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from state import EmailAgentState
from real_tools import get_google_tools


# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  # Updated to valid model name
    temperature=0.3,
    convert_system_message_to_human=True,
)


def react_agent_node(state: EmailAgentState) -> EmailAgentState:
    """
    ReAct agent that:
    1. Reads email
    2. Checks calendar if needed
    3. Drafts reply
    4. Creates action requiring HITL approval
    """

    print(f"\n🤖 REACT AGENT: Processing email from {state['email_from']}")

    email_body = state["email_body"].lower()
    email_subject = state["email_subject"].lower()

    # Get tools
    tools = get_google_tools()
    check_calendar_tool = tools[0]
    draft_email_tool = tools[2]

    # Detect meeting request
    meeting_keywords = ["meet", "schedule", "call", "sync", "discuss"]
    is_meeting_request = any(
        keyword in email_body or keyword in email_subject
        for keyword in meeting_keywords
    )

    calendar_info = ""
    pending_action = None

    # STEP 1 — Check calendar if meeting request (SAFE TOOL)
    if is_meeting_request:
        start_date, end_date = extract_date_range(state["email_body"])

        try:
            calendar_result = check_calendar_tool.invoke(
                {
                    "start_date": start_date,
                    "end_date": end_date,
                    "timezone": "Asia/Kolkata",
                }
            )

            calendar_info = calendar_result
            print("   ✓ Calendar checked")

        except Exception:
            calendar_info = "Could not check calendar."

    # STEP 2 — Draft reply using LLM
    prompt = f"""
You are an email assistant.

Original Email:
From: {state['email_from']}
Subject: {state['email_subject']}
Body: {state['email_body']}

Calendar Availability:
{calendar_info if calendar_info else "Not checked"}

Write a professional reply:
- Friendly and concise
- 2–3 paragraphs
- Suggest times if meeting request
- Sign off with 'Best regards'
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        draft_content = response.content
        print("   ✓ Draft created")

    except Exception as e:
        print(f"   ✗ Draft failed: {e}")
        draft_content = "Sorry, could not generate reply."

    # STEP 3 — Format email draft (SAFE TOOL)
    try:
        formatted_draft = draft_email_tool.invoke(
            {
                "recipient": state["email_from"],
                "subject": (
                    f"Re: {state['email_subject']}"
                    if not state["email_subject"].startswith("Re:")
                    else state["email_subject"]
                ),
                "body_content": draft_content,
                "original_subject": state["email_subject"],
            }
        )
    except Exception:
        formatted_draft = draft_content

    # STEP 4 — Create pending action (DANGEROUS → requires HITL)
    # Store draft at TOP LEVEL for easy Studio visibility
    pending_action = {
        "action_type": "send_email",  # Must match tool name in real_tools.py
        "to": state["email_from"],
        "subject": f"Re: {state['email_subject']}",
        "body": draft_content,  # ← DRAFT AT TOP LEVEL for Studio visibility
    }

    print("   📤 Action queued: send_email (requires approval)")
    print("   📝 Draft preview:", draft_content[:100] + "...")
    print("✓ ReAct agent completed")

    return {
        **state,
        # 🔥 TOP-LEVEL FIELD for Studio visibility
        "draft_reply": draft_content,
        "messages": [
            {
                "role": "assistant",
                "content": formatted_draft,
            }
        ],
        "pending_action": pending_action,
    }


def extract_date_range(email_body: str) -> tuple:
    """Extract simple date range from email."""

    body_lower = email_body.lower()
    today = datetime.now()

    if "tomorrow" in body_lower:
        start = today + timedelta(days=1)
        end = start + timedelta(days=1)

    elif "next week" in body_lower:
        days_until_monday = (7 - today.weekday()) % 7
        days_until_monday = 7 if days_until_monday == 0 else days_until_monday
        start = today + timedelta(days=days_until_monday)
        end = start + timedelta(days=5)

    else:
        start = today + timedelta(days=1)
        end = start + timedelta(days=5)

    return start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")
