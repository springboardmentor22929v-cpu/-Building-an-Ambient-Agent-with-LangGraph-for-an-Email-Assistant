import time
from typing import Literal

from dotenv import load_dotenv
load_dotenv(".env")

# --- GEMINI IMPORTS ---
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from langgraph.graph import StateGraph, START, END
from langgraph.store.base import BaseStore
from langgraph.types import interrupt, Command

from email_assistant.tools import get_tools, get_tools_by_name
from email_assistant.tools.gmail.prompt_templates import GMAIL_TOOLS_PROMPT
from email_assistant.tools.gmail.gmail_tools import mark_as_read
from email_assistant.prompts import triage_system_prompt, triage_user_prompt, agent_system_prompt_hitl_memory, default_triage_instructions, default_background, default_response_preferences, default_cal_preferences, MEMORY_UPDATE_INSTRUCTIONS, MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT
from email_assistant.schemas import State, RouterSchema, StateInput, UserPreferences
from email_assistant.utils import parse_gmail, format_for_display, format_gmail_markdown

# --- CRITICAL HELPER: Bulletproof Retry ---
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

# Get tools with Gmail tools
tools = get_tools(["send_email_tool", "schedule_meeting_tool", "check_calendar_tool", "Question", "Done"], include_gmail=True)
tools_by_name = get_tools_by_name(tools)

# --- MODEL SETUP (GEMINI) ---
llm_base = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
llm_router = llm_base.with_structured_output(RouterSchema) 
llm_with_tools = llm_base.bind_tools(tools)
llm_memory = llm_base.with_structured_output(UserPreferences)

def get_memory(store, namespace, default_content=None):
    user_preferences = store.get(namespace, "user_preferences")
    if user_preferences:
        return user_preferences.value
    else:
        store.put(namespace, "user_preferences", default_content)
        return default_content 

def update_memory(store, namespace, messages):
    user_preferences = store.get(namespace, "user_preferences")
    current_value = user_preferences.value if user_preferences else ""
    
    # Use Gemini + Safe Invoke
    print(f" >>> 🧠 Updating Memory for {namespace[1]}...")
    result = safe_invoke(llm_memory,
        [
            {"role": "system", "content": MEMORY_UPDATE_INSTRUCTIONS.format(current_profile=current_value, namespace=namespace)},
        ] + messages
    )
    store.put(namespace, "user_preferences", result.user_preferences)

# Nodes 
def triage_router(state: State, store: BaseStore) -> Command[Literal["triage_interrupt_handler", "response_agent", "__end__"]]:
    author, to, subject, email_thread, email_id = parse_gmail(state["email_input"])
    user_prompt = triage_user_prompt.format(author=author, to=to, subject=subject, email_thread=email_thread)
    email_markdown = format_gmail_markdown(subject, author, to, email_thread, email_id)
    triage_instructions = get_memory(store, ("email_assistant", "triage_preferences"), default_triage_instructions)
    
    system_prompt = triage_system_prompt.format(
        background=default_background,
        triage_instructions=triage_instructions,
    )

    # Use Safe Invoke
    print(" >>> 🧠 Triage: Asking Gemini...")
    result = safe_invoke(llm_router, [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    classification = result.classification

    if classification == "respond":
        print("📧 Classification: RESPOND - This email requires a response")
        goto = "response_agent"
        update = {
            "classification_decision": result.classification,
            "messages": [{"role": "user", "content": f"Respond to the email: {email_markdown}"}],
        }
    elif classification == "ignore":
        print("🚫 Classification: IGNORE - This email can be safely ignored")
        goto = END
        update = {"classification_decision": classification}
    elif classification == "notify":
        print("🔔 Classification: NOTIFY - This email contains important information") 
        goto = "triage_interrupt_handler"
        update = {"classification_decision": classification}
    else:
        raise ValueError(f"Invalid classification: {classification}")
    
    return Command(goto=goto, update=update)

def triage_interrupt_handler(state: State, store: BaseStore) -> Command[Literal["response_agent", "__end__"]]:
    author, to, subject, email_thread, email_id = parse_gmail(state["email_input"])
    email_markdown = format_gmail_markdown(subject, author, to, email_thread, email_id)
    messages = [{"role": "user", "content": f"Email to notify user about: {email_markdown}"}]

    request = {
        "action_request": {"action": f"Email Assistant: {state['classification_decision']}", "args": {}},
        "config": {"allow_ignore": True, "allow_respond": True, "allow_edit": False, "allow_accept": False},
        "description": email_markdown,
    }

    response = interrupt([request])[0]
    
    # Bulletproof parsing
    if not response or not isinstance(response, dict):
        response = {"type": "accept"}
    res_type = response.get("type", "accept")

    if res_type == "response":
        user_input = response.get("args", "Proceed")
        messages.append({"role": "user", "content": f"User wants to reply to the email. Use this feedback to respond: {user_input}"})
        update_memory(store, ("email_assistant", "triage_preferences"), [{"role": "user", "content": f"The user decided to respond to the email, so update the triage preferences to capture this."}] + messages)
        goto = "response_agent"
    elif res_type == "ignore":
        messages.append({"role": "user", "content": f"The user decided to ignore the email even though it was classified as notify. Update triage preferences to capture this."})
        update_memory(store, ("email_assistant", "triage_preferences"), messages)
        goto = END
    else:
        # Fallback if UI sends something weird
        goto = "response_agent"

    return Command(goto=goto, update={"messages": messages})

def llm_call(state: State, store: BaseStore):
    cal_preferences = get_memory(store, ("email_assistant", "cal_preferences"), default_cal_preferences)
    response_preferences = get_memory(store, ("email_assistant", "response_preferences"), default_response_preferences)

    print(" >>> 🧠 Agent: Thinking with Memory...")
    # Use Safe Invoke
    response = safe_invoke(llm_with_tools, 
        [
            {"role": "system", "content": agent_system_prompt_hitl_memory.format(
                tools_prompt=GMAIL_TOOLS_PROMPT,
                background=default_background,
                response_preferences=response_preferences, 
                cal_preferences=cal_preferences
            )}
        ] + state["messages"]
    )
    return {"messages": [response]}
    
def interrupt_handler(state: State, store: BaseStore) -> Command[Literal["llm_call", "__end__"]]:
    result = []
    goto = "llm_call"

    for tool_call in state["messages"][-1].tool_calls:
        hitl_tools = ["send_email_tool", "schedule_meeting_tool", "Question"]
        
        if tool_call["name"] not in hitl_tools:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
            continue
            
        email_input = state["email_input"]
        author, to, subject, email_thread, email_id = parse_gmail(email_input)
        original_email_markdown = format_gmail_markdown(subject, author, to, email_thread, email_id)
        tool_display = format_for_display(tool_call)
        description = original_email_markdown + tool_display

        config = {"allow_ignore": True, "allow_respond": True, "allow_edit": True, "allow_accept": True}
        if tool_call["name"] == "Question":
            config["allow_edit"] = False
            config["allow_accept"] = False

        request = {
            "action_request": {"action": tool_call["name"], "args": tool_call["args"]},
            "config": config,
            "description": description,
        }

        print(f" >>> ✋ HITL: Reviewing {tool_call['name']}...")
        
        # --- THE FIX IS HERE ---
        raw_response = interrupt([request])
        
        # Safely extract the data whether LangSmith sends a list or a dict!
        if isinstance(raw_response, list) and len(raw_response) > 0:
            response = raw_response[0]
        elif isinstance(raw_response, dict):
            response = raw_response
        else:
            response = {"type": "accept"}

        res_type = response.get("type", "accept")
        # ------------------------

        if res_type == "accept":
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})
                        
        elif res_type == "edit":
            tool = tools_by_name[tool_call["name"]]
            initial_tool_call = tool_call["args"]
            
            # Safely get edited args
            edited_args = response.get("args", {}).get("args", initial_tool_call)

            try:
                observation = tool.invoke(edited_args)
                
                ai_message = state["messages"][-1]
                current_id = tool_call["id"]
                updated_tool_calls = [tc for tc in ai_message.tool_calls if tc["id"] != current_id] + [{"type": "tool_call", "name": tool_call["name"], "args": edited_args, "id": current_id}]
                
                result.append(ai_message.model_copy(update={"tool_calls": updated_tool_calls}))
                result.append({"role": "tool", "content": observation, "tool_call_id": current_id})

                if tool_call["name"] == "send_email_tool":
                    update_memory(store, ("email_assistant", "response_preferences"), [{"role": "user", "content": f"User edited email response. Initial: {initial_tool_call}. Edited: {edited_args}. {MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT}."}])
                elif tool_call["name"] == "schedule_meeting_tool":
                    update_memory(store, ("email_assistant", "cal_preferences"), [{"role": "user", "content": f"User edited calendar invitation. Initial: {initial_tool_call}. Edited: {edited_args}. {MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT}."}])

            except ValidationError as e:
                print(f" >>> ⚠️ Tool Mismatch Detected. Auto-Accepting '{tool_call['name']}'...")
                observation = tool.invoke(tool_call["args"])
                result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})

        elif res_type == "ignore":
            if tool_call["name"] == "send_email_tool":
                result.append({"role": "tool", "content": "User ignored this email draft.", "tool_call_id": tool_call["id"]})
                goto = END
                update_memory(store, ("email_assistant", "triage_preferences"), state["messages"] + result + [{"role": "user", "content": f"The user ignored the email draft. Update triage preferences to ensure emails of this type are not classified as respond. {MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT}."}])
            elif tool_call["name"] == "schedule_meeting_tool":
                result.append({"role": "tool", "content": "User ignored this calendar meeting draft.", "tool_call_id": tool_call["id"]})
                goto = END
                update_memory(store, ("email_assistant", "triage_preferences"), state["messages"] + result + [{"role": "user", "content": f"The user ignored the calendar meeting draft. Update triage preferences. {MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT}."}])
            elif tool_call["name"] == "Question":
                result.append({"role": "tool", "content": "User ignored this question.", "tool_call_id": tool_call["id"]})
                goto = END
                update_memory(store, ("email_assistant", "triage_preferences"), state["messages"] + result + [{"role": "user", "content": f"The user ignored the Question. Update triage preferences. {MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT}."}])

        elif res_type == "response":
            user_feedback = response.get("args", "Proceed")
            if tool_call["name"] == "send_email_tool":
                result.append({"role": "tool", "content": f"User gave feedback to incorporate: {user_feedback}", "tool_call_id": tool_call["id"]})
                update_memory(store, ("email_assistant", "response_preferences"), state["messages"] + result + [{"role": "user", "content": f"User gave feedback to update response preferences. {MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT}."}])
            elif tool_call["name"] == "schedule_meeting_tool":
                result.append({"role": "tool", "content": f"User gave feedback to incorporate: {user_feedback}", "tool_call_id": tool_call["id"]})
                update_memory(store, ("email_assistant", "cal_preferences"), state["messages"] + result + [{"role": "user", "content": f"User gave feedback to update calendar preferences. {MEMORY_UPDATE_INSTRUCTIONS_REINFORCEMENT}."}])
            elif tool_call["name"] == "Question":
                result.append({"role": "tool", "content": f"User answered the question: {user_feedback}", "tool_call_id": tool_call["id"]})

    return Command(goto=goto, update={"messages": result})

def should_continue(state: State, store: BaseStore) -> Literal["interrupt_handler", "mark_as_read_node"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls: 
            if tool_call["name"] == "Done":
                return "mark_as_read_node"
            else:
                return "interrupt_handler"
    return "mark_as_read_node" # Fallback

def mark_as_read_node(state: State):
    email_input = state["email_input"]
    author, to, subject, email_thread, email_id = parse_gmail(email_input)
    mark_as_read(email_id)

# Build workflow
agent_builder = StateGraph(State)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("interrupt_handler", interrupt_handler)
agent_builder.add_node("mark_as_read_node", mark_as_read_node)
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, {"interrupt_handler": "interrupt_handler", "mark_as_read_node": "mark_as_read_node"})
agent_builder.add_edge("mark_as_read_node", END)
response_agent = agent_builder.compile()

overall_workflow = (
    StateGraph(State, input=StateInput)
    .add_node(triage_router)
    .add_node(triage_interrupt_handler)
    .add_node("response_agent", response_agent)
    .add_node("mark_as_read_node", mark_as_read_node)
    .add_edge(START, "triage_router")
    .add_edge("mark_as_read_node", END)
)

email_assistant = overall_workflow.compile()