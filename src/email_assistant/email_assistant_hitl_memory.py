import time
from typing import Literal, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import MessagesState, START, END, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver

from email_assistant.utils import parse_email, format_email_markdown, format_for_display
from email_assistant.prompts import (
    triage_system_prompt,
    triage_user_prompt,
    agent_system_prompt_hitl,
    default_background,
    default_triage_instructions,
    default_response_preferences,
    default_cal_preferences,
    MEMORY_UPDATE_INSTRUCTIONS,
    MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT
)
from email_assistant.tools.default.prompt_templates import HITL_MEMORY_TOOLS_PROMPT

# --- 1. SAFE RETRY HELPER ---
def safe_invoke(llm, input_data):
    """Retries the API call if it hits a rate limit."""
    while True:
        try:
            return llm.invoke(input_data)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f" >>> 🛑 RATE LIMIT HIT. Pausing for 60s... (Please wait)")
                time.sleep(60)
                print(" >>> 🟢 Resuming...")
            else:
                raise e

# --- 2. EXTENDED STATE ---
class State(MessagesState):
    email_input: dict
    classification_decision: Literal["ignore", "respond", "notify"]
    user_preferences: str 

# --- 3. Define Tools ---
@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    return f"Email sent to {to} with subject '{subject}'"

@tool
def schedule_meeting(
    attendees: List[str], 
    subject: str, 
    duration_minutes: int, 
    preferred_day: datetime, 
    start_time: int
) -> str:
    """Schedule a calendar meeting."""
    return f"Meeting '{subject}' scheduled."

@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability."""
    return f"Available times: 9:00 AM, 2:00 PM"

@tool
class Question(BaseModel):
      content: str
@tool
class Done(BaseModel):
      done: bool

# --- 4. Router ---
class RouterSchema(BaseModel):
    classification: Literal["ignore", "respond", "notify"]

llm_router = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0).with_structured_output(RouterSchema)

def triage_router(state: State) -> Command[Literal["triage_interrupt_handler", "response_agent", "__end__"]]:
    """Analyze email content."""
    preferences = state.get("user_preferences", "No specific preferences yet.")
    author, to, subject, email_thread = parse_email(state["email_input"])
    
    system_prompt = triage_system_prompt.format(
        background=default_background, 
        triage_instructions=default_triage_instructions
    )
    
    print(" >>> 🧠 Triage: Analyzing...")
    result = safe_invoke(llm_router, [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Email: {email_thread}\n\nUser Preferences to remember: {preferences}"},
    ])

    email_markdown = format_email_markdown(subject, author, to, email_thread)

    if result.classification == "respond":
        return Command(goto="response_agent", update={
            "classification_decision": "respond",
            "messages": [{"role": "user", "content": f"Respond to: {email_markdown}"}]
        })
    elif result.classification == "notify":
        return Command(goto="triage_interrupt_handler", update={"classification_decision": "notify"})
    else:
        return Command(goto=END, update={"classification_decision": "ignore"})

def triage_interrupt_handler(state: State) -> Command[Literal["response_agent", "__end__"]]:
    return Command(goto=END)

# --- 5. Response Agent ---
tools = [write_email, schedule_meeting, check_calendar_availability, Question, Done]
tools_by_name = {tool.name: tool for tool in tools}

llm_agent = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0).bind_tools(tools)

def llm_call(state: State):
    current_prefs = state.get("user_preferences", "")
    print(f" >>> 🧠 Agent: Thinking (Memory size: {len(current_prefs)} chars)...")
    
    prompt = agent_system_prompt_hitl_memory.format(
        tools_prompt=HITL_MEMORY_TOOLS_PROMPT,
        background=default_background,
        response_preferences=default_response_preferences + f"\n\nIMPORTANT - LEARNED USER PREFERENCES:\n{current_prefs}",
        cal_preferences=default_cal_preferences, 
    )
    
    response = safe_invoke(llm_agent, [{"role": "system", "content": prompt}] + state["messages"])
    return {"messages": [response]}

def update_memory(store, namespace, messages):
    """Simple memory update helper."""
    # We skip the LLM refinement for speed/stability in this specific fix
    # and just append the raw feedback to ensure it works.
    try:
        current = store.get(namespace, "user_preferences")
        curr_val = current.value if current else ""
        
        # Extract the last user message which contains the feedback
        if isinstance(messages, list) and messages:
             # Find the content in the list of messages
             feedback = str(messages)
             for m in reversed(messages):
                 if isinstance(m, dict) and "content" in m:
                     feedback = m["content"]
                     break
        else:
            feedback = str(messages)

        new_val = curr_val + f"\n- {feedback}"
        
        store.put(namespace, "user_preferences", new_val)
        print(f" >>> 🧠 MEMORY UPDATED successfully.")
    except Exception as e:
        print(f"Memory update failed (non-critical): {e}")

def interrupt_handler(state: State, store: MemorySaver) -> Command[Literal["llm_call", "__end__"]]:
    """HITL Handler that LEARNS and handles ERRORS."""
    result = []
    goto = "llm_call"
    
    for tool_call in state["messages"][-1].tool_calls:
        hitl_tools = ["write_email", "schedule_meeting", "Question"]
        
        if tool_call["name"] not in hitl_tools:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
            continue
        
        # Standard Setup
        email_input = state["email_input"]
        author, to, subject, email_thread = parse_email(email_input)
        original_email_markdown = format_email_markdown(subject, author, to, email_thread)
        tool_display = format_for_display(tool_call)
        description = original_email_markdown + tool_display

        request = {
            "action_request": {"action": tool_call["name"], "args": tool_call["args"]},
            "config": {"allow_ignore": True, "allow_respond": True, "allow_edit": True, "allow_accept": True},
            "description": description,
        }

        print(f" >>> ✋ HITL: Reviewing {tool_call['name']}...")
        response = interrupt([request])[0]

        if response["type"] == "accept":
            tool = tools_by_name[tool_call["name"]]
            res = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": res, "tool_call_id": tool_call["id"]})
                        
        elif response["type"] == "edit":
            tool = tools_by_name[tool_call["name"]]
            edited_args = response["args"]["args"]
            
            # --- CRITICAL FIX FOR VALIDATION ERROR ---
            try:
                # Try to execute with edited args
                res = tool.invoke(edited_args)
                
                # If successful, we update memory
                update_memory(store, ("email_assistant", "response_preferences"), [{
                    "role": "user",
                    "content": f"User edited {tool_call['name']}. They preferred: {edited_args}"
                }])
                result.append({"role": "tool", "content": res, "tool_call_id": tool_call["id"]})
                
            except ValidationError as e:
                # If validation fails, it means the user sent args for the WRONG tool.
                # Example: Sent "Subject/Body" (Email args) to "Schedule Meeting" tool.
                print(f" >>> ⚠️ Mismatch detected! User sent args for a different tool ({tool_call['name']}).")
                print(f" >>> Auto-Accepting '{tool_call['name']}' to move to the next tool.")
                
                # Run the ORIGINAL args (Ignore the edit for this specific tool)
                res = tool.invoke(tool_call["args"])
                result.append({"role": "tool", "content": res, "tool_call_id": tool_call["id"]})
            # -----------------------------------------

        elif response["type"] == "response":
            feedback = response["args"]
            update_memory(store, ("email_assistant", "response_preferences"), [{
                "role": "user",
                "content": f"User feedback on {tool_call['name']}: {feedback}"
            }])
            result.append({"role": "tool", "content": f"User feedback: {feedback}", "tool_call_id": tool_call["id"]})
            
        elif response["type"] == "ignore":
             result.append({"role": "tool", "content": "User ignored this.", "tool_call_id": tool_call["id"]})
             goto = END

    return Command(goto=goto, update={"messages": result})

def should_continue(state: State):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        for tc in last_message.tool_calls:
            if tc["name"] == "Done": return END
        return "interrupt_handler"
    return END

# --- 6. Build Graph ---
builder = StateGraph(State)
builder.add_node("llm_call", llm_call)
builder.add_node("interrupt_handler", interrupt_handler)
builder.add_edge(START, "llm_call")
builder.add_conditional_edges("llm_call", should_continue, {"interrupt_handler": "interrupt_handler", END: END})
response_agent = builder.compile()

overall = StateGraph(State)
overall.add_node(triage_router)
overall.add_node(triage_interrupt_handler)
overall.add_node("response_agent", response_agent)
overall.add_edge(START, "triage_router")

email_assistant_memory = overall.compile(checkpointer=MemorySaver(), store=MemorySaver())