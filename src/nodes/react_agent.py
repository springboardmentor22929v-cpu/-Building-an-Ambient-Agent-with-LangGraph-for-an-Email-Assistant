from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.state import EmailAgentState
from src.tools.google_tools import get_google_tools
from datetime import datetime, timedelta

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    convert_system_message_to_human=True
)


def react_agent_node(state: EmailAgentState) -> EmailAgentState:
    """
    ReAct agent that creates actions requiring HITL approval.
    """
    print(f"\n🤖 REACT AGENT: Processing email from {state['email_from']}")

    email_body = state['email_body'].lower()
    email_subject = state['email_subject'].lower()

    tools = get_google_tools()
    check_calendar_tool = tools[0]
    draft_email_tool = tools[2]

    # Detect meeting request
    meeting_keywords = ['meet', 'schedule', 'call', 'sync', 'catch up', 'discuss']
    is_meeting_request = any(
        keyword in email_body or keyword in email_subject
        for keyword in meeting_keywords
    )

    calendar_info = ""

    # Step 1: Check calendar if needed (safe action)
    if is_meeting_request:
        start_date, end_date = extract_date_range(state['email_body'])

        try:
            calendar_result = check_calendar_tool.invoke({
                "start_date": start_date,
                "end_date": end_date,
                "timezone": "Asia/Kolkata"
            })
            calendar_info = calendar_result
            print("   ✓ Calendar checked")

        except Exception as e:
            calendar_info = "Could not check calendar."

    # Step 2: Generate draft body content
    draft_context = f"""Draft a professional email reply.

Original Email:
From: {state['email_from']}
Subject: {state['email_subject']}
Body: {state['email_body']}

{f"My Calendar Availability:{chr(10)}{calendar_info}" if calendar_info else ""}

Instructions:
- Write ONLY the email body (no subject line, no "To:" header)
- Professional but friendly tone
- Concise (2-3 short paragraphs)
- Use DD-MM-YYYY date format for any dates
- If meeting request with calendar info, suggest 2-3 specific times
- End with "Best regards"
- Do NOT include Subject: or To: lines in your response

Write the email body only:"""

    try:
        draft_response = llm.invoke(draft_context)

        # Get ONLY the body content (no headers)
        body_content = draft_response.content.strip()

        # Remove any accidental headers the LLM might add
        lines = body_content.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip lines that look like email headers
            if line.startswith("Subject:"):
                continue
            if line.startswith("To:"):
                continue
            if line.startswith("From:"):
                continue
            cleaned_lines.append(line)

        body_content = '\n'.join(cleaned_lines).strip()

        print("   ✓ Draft created")

    except Exception as e:
        body_content = "I would be happy to help. Please let me know how I can assist."
        print(f"   ✗ Error creating draft: {e}")

    # Step 3: Build clean formatted preview (for display only)
    subject = f"Re: {state['email_subject']}" if not state['email_subject'].startswith('Re:') else state['email_subject']

    formatted_preview = f"""To: {state['email_from']}
Subject: {subject}

{body_content}"""

    # Step 4: Create pending action (DANGEROUS - requires HITL)
    pending_action = {
        "action_type": "send_email_reply",
        "args": {
            "recipient": state['email_from'],
            "subject": subject,
            "body": body_content,
            "draft_preview": formatted_preview
        }
    }

    print(f"   📤 Action queued: send_email_reply (requires approval)")

    messages = [
        {
            "role": "assistant",
            "content": formatted_preview,
            "metadata": {
                "is_meeting_request": is_meeting_request,
                "calendar_checked": bool(calendar_info),
                "body_only": body_content
            }
        }
    ]

    return {
        **state,
        "messages": messages,
        "pending_action": pending_action
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