import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")

def triage_node(state):
    """Decide if email should be ignored, notify human, or respond/act"""
    text = state["email"].lower()
    new_state = state.copy()
    if "sale" in text or "discount" in text:
        new_state["triage"] = "ignore"
    elif "exam" in text:
        new_state["triage"] = "notify_human"
    else:
        new_state["triage"] = "respond/act"
    print("Triage result:", new_state["triage"])
    return new_state

def react_node(state):
    """Take action based on triage decision"""
    if state["triage"] != "respond/act":
        return state

    if "meeting" in state["email"].lower():
        availability = "Tomorrow at 3 PM is free."
        new_state = state.copy()
        new_state["observation"] = availability
        print("Checked calendar:", availability)
        print("Draft reply: I am available tomorrow at 3 PM.")
        return new_state

    return state

def end_node(state):
    """Final node"""
    print("Final state:", state)
    return state

graph = StateGraph(dict)

graph.add_node("triage", triage_node)
graph.add_node("react", react_node)
graph.add_node("end", end_node)

graph.set_entry_point("triage")
graph.add_edge("triage", "react")
graph.add_edge("react", "end")
graph.add_edge("end", END)

app = graph.compile()
if __name__ == "__main__":
    emails = [
        "Meeting request: Can we meet tomorrow at 4 PM?",
        "Big SALE today! Get 50% off everything!",
        "Exam schedule released for next week"
    ]

    for email in emails:
        print("\n Processing email:", email)
        initial_state = {
            "email": email,
            "triage": None,
            "observation": None
        }
        result = app.invoke(initial_state)
        print("Result:", result)