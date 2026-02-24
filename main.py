from src.graph import build_graph
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    graph = build_graph()

    # ---- Get User Input ----
    subject = input("Enter email subject: ")
    body = input("Enter email body: ")

    # ---- Initial State ----
    initial_state = {
        "email_id": None,
        "email_from": "sender@example.com",
        "email_subject": subject,
        "email_body": body,

        "triage_decision": None,
        "triage_reasoning": None,

        "messages": None,

        "pending_action": None,
        "requires_approval": False,
        "human_decision": None,
        "human_feedback": None,

        "execution_result": None,
        "execution_status": None,

        "user_preferences": {},
        "memory_saved": False,

        "workflow_id": None
    }

    # ---- Invoke Graph with thread_id ----
    result = graph.invoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": "demo-thread-1"
            }
        }
    )

    print("\n📦 FINAL RESULT:")
    print(result)


if __name__ == "__main__":
    main()
