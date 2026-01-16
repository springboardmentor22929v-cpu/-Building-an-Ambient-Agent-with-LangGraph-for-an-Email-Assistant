from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.state import EmailAgentState
from src.tools.mock_tools import read_calendar, search_past_emails, draft_email_reply

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    convert_system_message_to_human=True
)

def react_agent_node(state: EmailAgentState) -> EmailAgentState:
    """
    ReAct agent that drafts email responses.
    For Milestone 1, this is a simplified version without full tool calling.
    We'll add proper ReAct with tools in Milestone 3.
    """
    print(f"\n🤖 REACT AGENT: Processing email from {state['email_from']}")
    
    # Step 1: Analyze if we need calendar info
    needs_calendar = "meet" in state['email_body'].lower() or "schedule" in state['email_body'].lower()
    
    calendar_info = ""
    if needs_calendar:
        print("  Detected meeting request - checking calendar")
        # Mock calendar check
        calendar_info = "\n\nAvailable times this week: Tuesday 2pm, Wednesday 10am, Thursday 3pm"
    
    # Step 2: Check for past context
    past_context = ""
    if state.get('email_from'):
        print("  Searching past emails for context")
        # Mock search
        if "colleague" in state['email_from']:
            past_context = "\n\nContext: You've previously discussed the Q4 project with this person."
    
    # Step 3: Draft the reply
    print("   Drafting reply")
    
    draft_prompt = f"""You are a helpful email assistant. Draft a professional reply to this email:

From: {state['email_from']}
Subject: {state['email_subject']}
Body: {state['email_body']}
{calendar_info}
{past_context}

Guidelines:
- Be professional but friendly
- Keep it concise (2-3 paragraphs)
- Address all questions/requests in the email
- If it's a meeting request, propose specific times from the calendar
- Sign off appropriately

Draft reply:"""

    # Generate response
    response = llm.invoke(draft_prompt)
    draft = response.content
    
    print(f"✓ Draft completed")
    print(f"  Preview: {draft[:100]}...")
    
    # Store in messages format
    messages = [
        {
            "role": "assistant",
            "content": draft,
            "metadata": {
                "used_calendar": needs_calendar,
                "has_context": bool(past_context)
            }
        }
    ]
    
    return {
        **state,
        "messages": messages
    }