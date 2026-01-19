from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.agents.state import EmailAgentState
from src.tools.google_tools import get_google_tools

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    convert_system_message_to_human=True
)

# Bind tools to LLM (if supported, otherwise use manual approach)
def react_agent_node(state: EmailAgentState) -> EmailAgentState:
    """
    ReAct agent with Google tools integration.
    """
    print(f"\n🤖 REACT AGENT: Processing email from {state['email_from']}")
    
    # Get tools
    tools = get_google_tools()
    tool_dict = {tool.name: tool for tool in tools}
    
    # Initialize messages
    messages = state.get("messages", [])
    
    if not messages:
        # Initial prompt
        initial_prompt = f"""You are an email assistant helping respond to this email:

From: {state['email_from']}
Subject: {state['email_subject']}
Body: {state['email_body']}

Available tools:
1. check_calendar - Check available time slots
2. schedule_meeting - Create calendar events  
3. draft_email_reply - Draft professional email responses

Your goal: Help respond to this email appropriately.

If it's a meeting request:
- Use check_calendar to find available times
- Draft a reply suggesting those times
- DO NOT schedule meetings without explicit confirmation

If it's a question or request:
- Draft an appropriate reply using draft_email_reply

Think step by step. What should you do first?"""
        
        messages.append(HumanMessage(content=initial_prompt))
    
    # Simple ReAct loop (without bind_tools)
    max_iterations = 5
    
    for iteration in range(max_iterations):
        print(f"\n  🔄 Iteration {iteration + 1}/{max_iterations}")
        
        # Get LLM response
        try:
            response = llm.invoke(messages[-1:])
            messages.append(response)
        except Exception as e:
            print("⚠️ Gemini stopped generation early (safe to ignore)")
            break

        
        # Check if response wants to use tools
        # Simple keyword detection (production would use function calling)
        content = response.content.lower()
        
        tool_used = False
        
        # Check for tool usage keywords
        if "check_calendar" in content or "check my calendar" in content:
            print(f"  🛠️  Detected: check_calendar needed")
            # Extract dates from context or use default
            from datetime import datetime, timedelta
            today = datetime.now()
            next_week = today + timedelta(days=7)
            
            result = tools[0].invoke({  # check_calendar
                "start_date": today.strftime("%d-%m-%Y"),
                "end_date": next_week.strftime("%d-%m-%Y")
            })
            
            messages.append(HumanMessage(content=f"Calendar availability:\n{result}\nPlease draft a professional reply suggesting suitable times."))
            tool_used = True
        
        elif "draft_email" in content or "draft a reply" in content:
            print(f"  ✍️  Agent wants to draft email")
            # Let the agent's response be the draft
            break
        
        if not tool_used:
            # Agent is done or gave final answer
            break
    
    print(f"✓ ReAct agent completed")
    
    return {
        **state,
        "messages": messages
    }