import os
from langsmith import Client
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from mock_llm import MockLLM
import tools

# Load environment variables
load_dotenv()

# Initialize LangSmith client
client = Client()

llm = MockLLM()

def triage_node(state):
    email = state["email"]
    decision = llm.classify(email["subject"], email["body"])
    state["triage"] = decision
    state["trace"].append({"step": "triage", "decision": decision})
    return state

def act_node(state):
    triage = state["triage"]
    email = state["email"]

    if triage == "ignore":
        state["result"] = tools.archive_email(email["subject"])
    elif triage == "notify_human":
        state["result"] = tools.notify_human(email["subject"])
    else:
        draft = llm.draft_reply(email["subject"], email["sender"])
        state["result"] = tools.send_draft(draft)

    state["trace"].append({"step": "act", "result": state["result"]})
    return state

def build_graph():
    graph = StateGraph(dict)
    graph.add_node("triage", triage_node)
    graph.add_node("act", act_node)
    graph.set_entry_point("triage")
    graph.add_edge("triage", "act")
    graph.add_edge("act", END)
    return graph.compile()