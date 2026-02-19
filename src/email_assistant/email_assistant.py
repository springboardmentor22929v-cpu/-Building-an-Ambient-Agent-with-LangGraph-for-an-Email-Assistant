import time
from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field

# Import specific Google error handling
from google.api_core.exceptions import ResourceExhausted

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import MessagesState, START, END, StateGraph
from langgraph.types import Command

from email_assistant.utils import parse_email, format_email_markdown
from email_assistant.prompts import (
    triage_system_prompt,
    triage_user_prompt,
    default_triage_instructions,
    default_background,
    agent_system_prompt,
    default_response_preferences,
    default_cal_preferences,
)
from email_assistant.tools.default.prompt_templates import AGENT_TOOLS_PROMPT

# --- HELPER: The Bulletproof Retry Function ---
def safe_invoke(llm, input_data):
    """
    Invokes the LLM. If it hits a Rate Limit (429), it waits 60s and tries again.
    It will keep trying forever until it succeeds.
    """
    while True:
        try:
            return llm.invoke(input_data)
        except Exception as e:
            # Check if the error string contains "429" or "Resource"
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f" >>> HIT RATE LIMIT. Sleeping 60 seconds before retrying...")
                time.sleep(60)
            else:
                # If it's a different error (like code error), raise it
                raise e

# --- 1. Define Tools (Now with Docstrings!) ---
@tool
def write_email(to: str, subject: str, content: str) -> str:
    """Write and send an email."""
    return f"Email sent to {to} with subject '{subject}' and content: {content}"

@tool
def schedule_meeting(attendees: list, subject: str, duration_minutes: int, preferred_day: datetime, start_time: int):
    """Schedule a calendar meeting."""
    date_str = preferred_day.strftime("%A, %B %d, %Y")
    return f"Meeting '{subject}' scheduled on {date_str}"

@tool
def check_calendar_availability(day: str) -> str:
    """Check calendar availability for a given day."""
    return f"Available times on {day}: 9:00 AM, 2:00 PM"

@tool
class Done(BaseModel):
      """Mark the email task as done."""
      done: bool

# --- 2. Define State ---
class State(MessagesState):
    email_input: dict
    classification_decision: Literal["ignore", "respond", "notify"]

# --- 3. Define Router ---
class RouterSchema(BaseModel):
    reasoning: str = Field(description="Reasoning")
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="The classification of an email."
    )

# Using gemini-2.5-flash as it is available to you
llm_router = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0).with_structured_output(RouterSchema)

def triage_router(state: State) -> Command[Literal["response_agent", "__end__"]]:
    author, to, subject, email_thread = parse_email(state["email_input"])
    system_prompt = triage_system_prompt.format(background=default_background, triage_instructions=default_triage_instructions)
    user_prompt = triage_user_prompt.format(author=author, to=to, subject=subject, email_thread=email_thread)
    
    # !!! USE SAFE INVOKE !!!
    result = safe_invoke(llm_router, [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    if result.classification == "respond":
        goto = "response_agent"
        update = {
            "messages": [{"role": "user", "content": f"Respond: \n\n{format_email_markdown(subject, author, to, email_thread)}"}],
            "classification_decision": result.classification,
        }
    else:
        goto = END
        update = {"classification_decision": result.classification}
        
    return Command(goto=goto, update=update)

# --- 4. Response Agent ---
tools = [write_email, schedule_meeting, check_calendar_availability, Done]
tools_by_name = {tool.name: tool for tool in tools}

llm_agent = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0).bind_tools(tools)

def llm_call(state: State):
    # !!! USE SAFE INVOKE !!!
    response = safe_invoke(llm_agent, 
        [{"role": "system", "content": agent_system_prompt.format(
            tools_prompt=AGENT_TOOLS_PROMPT,
            background=default_background,
            response_preferences=default_response_preferences,
            cal_preferences=default_cal_preferences, 
        )}] + state["messages"]
    )
    return {"messages": [response]}

def tool_handler(state: State):
    result = []
    if state["messages"][-1].tool_calls:
        for tool_call in state["messages"][-1].tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content" : str(observation), "tool_call_id": tool_call["id"]})
    return {"messages": result}

def should_continue(state: State) -> Literal["tool_handler", "__end__"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls: 
            if tool_call["name"] == "Done":
                return END
        return "tool_handler"
    return END

# --- 5. Compile Graph ---
workflow_agent = StateGraph(State)
workflow_agent.add_node("llm_call", llm_call)
workflow_agent.add_node("tool_handler", tool_handler)
workflow_agent.add_edge(START, "llm_call")
workflow_agent.add_conditional_edges("llm_call", should_continue, {"tool_handler": "tool_handler", END: END})
workflow_agent.add_edge("tool_handler", "llm_call")
agent = workflow_agent.compile()

email_assistant = (
    StateGraph(State)
    .add_node(triage_router)
    .add_node("response_agent", agent)
    .add_edge(START, "triage_router")
).compile()