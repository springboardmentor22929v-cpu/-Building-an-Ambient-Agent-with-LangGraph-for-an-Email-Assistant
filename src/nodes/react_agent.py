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
    
    # Get tools
    tools = get_google_tools()
    check_calendar_tool = tools[0]
    schedule_meeting_tool = tools[1]
    draft_email_tool = tools[2]
    
    # Detect meeting request
    meeting_keywords = ['meet', 'schedule', 'call', 'sync', 'catch up', 'discuss']
    is_meeting_request = any(keyword in email_body or keyword in email_subject for keyword in meeting_keywords)
    
    calendar_info = ""
    pending_action = None
    
    # Step 1: Check calendar if meeting request (safe - auto-execute)
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
    
    # Step 2: Draft email (safe - auto-execute)
    draft_context = f"""Draft a professional email reply.

Original Email:
From: {state['email_from']}
Subject: {state['email_subject']}
Body: {state['email_body']}

{f"Calendar Availability:\n{calendar_info}" if calendar_info else ""}

Instructions:
- Professional but friendly tone
- Concise (2-3 paragraphs)
- Use DD-MM-YYYY date format
- If meeting request, suggest 2-3 specific times
- Sign off with "Best regards"

Draft:"""

    try:
        draft_response = llm.invoke(draft_context)
        draft_content = draft_response.content
        
        formatted_draft = draft_email_tool.invoke({
            "recipient": state['email_from'],
            "subject": f"Re: {state['email_subject']}" if not state['email_subject'].startswith('Re:') else state['email_subject'],
            "body_content": draft_content,
            "original_subject": state['email_subject']
        })
        
        print("   ✓ Draft created")
        
    except Exception as e:
        formatted_draft = f"Error: {e}"
        print(f"   ✗ Error creating draft")
        draft_content = ""
    
    # Step 3: Determine what action to take
    # For email replies, sending is DANGEROUS - requires approval
    
    if is_meeting_request:
        # Meeting request: Create action to SEND email with meeting proposal
        action_type = "send_email_reply"  # DANGEROUS - requires HITL
        
        pending_action = {
            "action_type": action_type,
            "args": {
                "recipient": state['email_from'],
                "subject": f"Re: {state['email_subject']}",
                "body": draft_content,
                "draft_preview": formatted_draft
            }
        }
        
        print(f"   📤 Action queued: {action_type} (requires approval)")
        
    else:
        # Simple question: Also requires approval before sending
        action_type = "send_email_reply"  # DANGEROUS
        
        pending_action = {
            "action_type": action_type,
            "args": {
                "recipient": state['email_from'],
                "subject": f"Re: {state['email_subject']}",
                "body": draft_content,
                "draft_preview": formatted_draft
            }
        }
        
        print(f"   📤 Action queued: {action_type} (requires approval)")
    
    # Store results
    messages = [
        {
            "role": "assistant",
            "content": formatted_draft,
            "metadata": {
                "is_meeting_request": is_meeting_request,
                "calendar_checked": bool(calendar_info)
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