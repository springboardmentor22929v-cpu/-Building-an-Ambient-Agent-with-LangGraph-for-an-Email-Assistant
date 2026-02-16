from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.state import EmailAgentState
from src.tools.google_tools import get_safe_tools
from src.agents.prompts import HITL_SYSTEM_PROMPT
from datetime import datetime, timedelta


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    convert_system_message_to_human=True
)


def react_agent_node(state: EmailAgentState) -> EmailAgentState:
    """
    ReAct agent that follows the HITL system prompt rules.

    1. Builds context from state (email details + today's date).
    2. Calls safe tools (check_calendar, etc.) if the email context
       suggests they are needed (e.g. meeting request → check calendar first).
    3. Invokes the LLM with the HITL system prompt.
    4. Parses the NEED_HUMAN_APPROVAL + DRAFT_EMAIL output.
    5. Returns a pending_action dict for the HITL checkpoint.
    """
    print(f"\n🤖 REACT AGENT: Analyzing action for {state['email_from']}")

    # ── 1. Gather context ───────────────────────────────────────────
    today = datetime.now()
    context_parts = [
        f"CURRENT DATE: {today.strftime('%A, %B %d, %Y')}",
        f"CURRENT TIME: {today.strftime('%H:%M')}",
        "",
        "EMAIL TO PROCESS:",
        f"From: {state['email_from']}",
        f"Subject: {state['email_subject']}",
        f"Body: {state['email_body']}",
    ]

    # ── 2. Optionally call safe tools for extra context ─────────────
    body_lower = state['email_body'].lower()
    safe_tools = {t.name: t for t in get_safe_tools()}

    # If the email mentions a meeting / schedule / availability, check calendar
    meeting_keywords = ['meeting', 'schedule', 'availability', 'calendar',
                        'call', 'catchup', 'catch up', 'dry run', 'time slot']
    if any(kw in body_lower for kw in meeting_keywords):
        if 'check_calendar' in safe_tools:
            try:
                start, end = extract_date_range(state['email_body'])
                print(f"   🔧 Auto-calling: check_calendar({start}, {end})")
                cal_result = safe_tools['check_calendar'].invoke({
                    "start_date": start,
                    "end_date": end,
                })
                context_parts.append(f"\nCALENDAR AVAILABILITY:\n{cal_result}")
            except Exception as e:
                print(f"   ⚠️  Calendar check failed: {e}")

    context = "\n".join(context_parts)

    # ── 3. Invoke LLM ──────────────────────────────────────────────
    messages = [
        {"role": "system", "content": HITL_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]

    response = llm.invoke(messages)
    content = response.content

    first_line = content.strip().splitlines()[0] if content else "(empty)"
    print(f"   LLM response (first line): {first_line}")

    # ── 4. Parse for HITL action ────────────────────────────────────
    pending_action = None
    if "NEED_HUMAN_APPROVAL" in content:
        try:
            if "DRAFT_EMAIL:" in content:
                draft_part = content.split("DRAFT_EMAIL:", 1)[1]
                # Trim trailing instruction text
                for sentinel in ["Do NOT", "WAIT for", "Do not", "---"]:
                    if sentinel in draft_part:
                        draft_part = draft_part.split(sentinel, 1)[0]
                draft_part = draft_part.strip()

                pending_action = {
                    "action_type": "send_email_reply",
                    "args": {
                        "recipient": state['email_from'],
                        "subject": f"Re: {state['email_subject']}",
                        "body": draft_part,
                        "draft_preview": draft_part,
                    }
                }
                print(f"   ⚠️  Action queued for approval: send_email_reply")
        except Exception as e:
            print(f"   ✗ Error parsing LLM response: {e}")

    return {
        **state,
        "messages": [{"role": "assistant", "content": content}],
        "pending_action": pending_action,
    }


def extract_date_range(email_body: str) -> tuple:
    """Extract date range from email or return defaults."""
    body_lower = email_body.lower()
    today = datetime.now()

    if 'tomorrow' in body_lower:
        start = today + timedelta(days=1)
        end = start + timedelta(days=1)
    elif 'next week' in body_lower:
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        start = today + timedelta(days=days_until_monday)
        end = start + timedelta(days=5)
    else:
        start = today + timedelta(days=1)
        end = start + timedelta(days=5)

    return start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")