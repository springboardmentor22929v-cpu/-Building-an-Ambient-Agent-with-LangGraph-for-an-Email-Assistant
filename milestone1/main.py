import csv
from langgraph.graph import StateGraph, END
from emails import emails

# -----------------------------
# Mock Gemini triage function
# -----------------------------
def mock_gemini_triage(email):
    """
    A simple mock classifier for emails.
    Returns:
        ignore       -> for spam or promotional emails
        notify_human -> for exams, HR updates, or important notifications
        respond      -> for personal messages, meetings, etc.
    """
    text = email.lower()
    if "sale" in text or "discount" in text or "promo" in text or "spam" in text:
        return "ignore"
    elif "exam" in text or "deadline" in text or "schedule" in text or "statement" in text:
        return "notify_human"
    else:
        return "respond"

# -----------------------------
# Triage node for LangGraph
# -----------------------------
def triage_node(state):
    email = state["email"]
    decision = mock_gemini_triage(email)
    state["triage"] = decision
    print("Mock triage:", decision)
    return state

# -----------------------------
# Setup LangGraph
# -----------------------------
graph = StateGraph(dict)
graph.add_node("triage", triage_node)
graph.set_entry_point("triage")
graph.add_edge("triage", END)
app = graph.compile()

# -----------------------------
# Run triage on 40 draft emails
# -----------------------------
if __name__ == "__main__":
    results = []
    for email in emails:
        out = app.invoke({"email": email})
        results.append([email, out["triage"]])

    # Save CSV
    with open("triage_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Email", "Category"])
        writer.writerows(results)

    print("Saved triage_dataset.csv with 40 labeled emails")
