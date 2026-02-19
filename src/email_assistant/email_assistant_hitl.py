import time
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Import specific Google error handling
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import MessagesState, START, END, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver

from email_assistant.utils import parse_email, format_email_markdown, format_for_display
from email_assistant.prompts import (
    triage_system_prompt,
    triage_user_prompt,
    default_triage_instructions,
    default_background,
    agent_system_prompt_hitl,
    default_response_preferences,
    default_cal_preferences,
)
from email_assistant.tools.default.prompt_templates import HITL_TOOLS_PROMPT

# --- 1. SAFE RETRY HELPER ---
def safe_invoke(llm, input_data):
    """
    Retries the API call if it hits a rate limit.
    Gemini 2.5 Flash has a limit of ~5 RPM, so we need a long sleep.
    """
    while True:
        try:
            return llm.invoke(input_data)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f" >>> 🛑 RATE LIMIT HIT (Gemini 2.5). Sleeping 60s to recharge... (Please wait)")
                time.sleep(60)
                print(" >>> 🟢 Resuming...")
            else:
                raise e

# --- 2. Define Tools ---
@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    return f"Email sent to {to} with subject '{subject}'"

@tool
def schedule_meeting(attendees: list, subject: str, duration_minutes: int, preferred_day: datetime, start_time: int):
    """Schedule a calendar meeting."""
    return f"Meeting '{subject}' scheduled."

@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability."""
    return f"Available times: 9:00 AM, 2:00 PM"

@tool
class Question(BaseModel):
      """Question to ask user."""
      content: str

@tool
class Done(BaseModel):
      """Mark as done."""
      done: bool

# --- 3. Define State ---
class State(MessagesState):
    email_input: dict
    classification_decision: Literal["ignore", "respond", "notify"]

# --- 4. Define Router ---
class RouterSchema(BaseModel):
    reasoning: str = Field(description="Reasoning")
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="The classification of an email."
    )

# !!! USING: gemini-2.5-flash !!!
llm_router = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0).with_structured_output(RouterSchema)

def triage_router(state: State) -> Command[Literal["triage_interrupt_handler", "response_agent", "__end__"]]:
    """Analyze email content."""
    
    author, to, subject, email_thread = parse_email(state["email_input"])
    system_prompt = triage_system_prompt.format(background=default_background, triage_instructions=default_triage_instructions)
    user_prompt = triage_user_prompt.format(author=author, to=to, subject=subject, email_thread=email_thread)
    
    # Use safe invoke
    result = safe_invoke(llm_router, [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    email_markdown = format_email_markdown(subject, author, to, email_thread)

    if result.classification == "respond":
        goto = "response_agent"
        update = {
            "classification_decision": result.classification,
            "messages": [{"role": "user", "content": f"Respond to the email: {email_markdown}"}],
        }
    elif result.classification == "ignore":
        goto = END
        update = {"classification_decision": result.classification}
    elif result.classification == "notify":
        goto = "triage_interrupt_handler"
        update = {"classification_decision": result.classification}
    else:
        raise ValueError(f"Invalid classification: {result.classification}")
        
    return Command(goto=goto, update=update)

def triage_interrupt_handler(state: State) -> Command[Literal["response_agent", "__end__"]]:
    """Handles interrupts from the triage step"""
    author, to, subject, email_thread = parse_email(state["email_input"])
    email_markdown = format_email_markdown(subject, author, to, email_thread)
    
    messages = [{"role": "user", "content": f"Email to notify user about: {email_markdown}"}]

    request = {
        "action_request": {"action": f"Email Assistant: {state['classification_decision']}", "args": {}},
        "config": {"allow_ignore": True, "allow_respond": True, "allow_edit": False, "allow_accept": False},
        "description": email_markdown,
    }

    response = interrupt([request])[0]

    if response["type"] == "response":
        user_input = response["args"]
        messages.append({"role": "user", "content": f"User wants to reply: {user_input}"})
        goto = "response_agent"
    elif response["type"] == "ignore":
        goto = END
    else:
        raise ValueError(f"Invalid response: {response}")

    return Command(goto=goto, update={"messages": messages})

# --- 5. Response Agent ---
tools = [write_email, schedule_meeting, check_calendar_availability, Question, Done]
tools_by_name = {tool.name: tool for tool in tools}

# !!! USING: gemini-2.5-flash !!!
llm_agent = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0).bind_tools(tools)

def llm_call(state: State):
    
    response = safe_invoke(llm_agent, 
        [{"role": "system", "content": agent_system_prompt_hitl.format(
            tools_prompt=HITL_TOOLS_PROMPT,
            background=default_background,
            response_preferences=default_response_preferences,
            cal_preferences=default_cal_preferences, 
        )}] + state["messages"]
    )
    return {"messages": [response]}

def interrupt_handler(state: State) -> Command[Literal["llm_call", "__end__"]]:
    """Creates an interrupt for human review of tool calls"""
    result = []
    goto = "llm_call"

    for tool_call in state["messages"][-1].tool_calls:
        hitl_tools = ["write_email", "schedule_meeting", "Question"]
        
        if tool_call["name"] not in hitl_tools:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
            continue
            
        email_input = state["email_input"]
        author, to, subject, email_thread = parse_email(email_input)
        original_email_markdown = format_email_markdown(subject, author, to, email_thread)
        tool_display = format_for_display(tool_call)
        description = original_email_markdown + tool_display

        config = {"allow_ignore": True, "allow_respond": True, "allow_edit": True, "allow_accept": True}
        if tool_call["name"] == "Question":
             config = {"allow_ignore": True, "allow_respond": True, "allow_edit": False, "allow_accept": False}

        request = {
            "action_request": {"action": tool_call["name"], "args": tool_call["args"]},
            "config": config,
            "description": description,
        }

        response = interrupt([request])[0]

        if response["type"] == "accept":
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
                        
        elif response["type"] == "edit":
            tool = tools_by_name[tool_call["name"]]
            edited_args = response["args"]["args"]
            ai_message = state["messages"][-1]
            current_id = tool_call["id"]
            
            updated_tool_calls = [tc for tc in ai_message.tool_calls if tc["id"] != current_id] + [
                {"type": "tool_call", "name": tool_call["name"], "args": edited_args, "id": current_id}
            ]
            
            result.append(ai_message.model_copy(update={"tool_calls": updated_tool_calls}))
            observation = tool.invoke(edited_args)
            result.append({"role": "tool", "content": observation, "tool_call_id": current_id})
            
        elif response["type"] == "ignore":
            result.append({"role": "tool", "content": "User ignored this. End workflow.", "tool_call_id": tool_call["id"]})
            goto = END
            
        elif response["type"] == "response":
            user_feedback = response["args"]
            result.append({"role": "tool", "content": f"User feedback: {user_feedback}", "tool_call_id": tool_call["id"]})

    return Command(goto=goto, update={"messages": result})

def should_continue(state: State) -> Literal["interrupt_handler", "__end__"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls: 
            if tool_call["name"] == "Done":
                return END
        return "interrupt_handler"
    return END

# --- 6. Build the Graph ---
agent_builder = StateGraph(State)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("interrupt_handler", interrupt_handler)
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, {"interrupt_handler": "interrupt_handler", END: END})

response_agent = agent_builder.compile()

overall_workflow = (
    StateGraph(State)
    .add_node(triage_router)
    .add_node(triage_interrupt_handler)
    .add_node("response_agent", response_agent)
    .add_edge(START, "triage_router")
)

email_assistant = overall_workflow.compile()