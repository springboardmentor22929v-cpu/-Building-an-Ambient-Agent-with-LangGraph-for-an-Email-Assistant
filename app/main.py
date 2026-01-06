from app.agent.triage import triage_email
from app.agent.react_loop import react_loop

if __name__ == "__main__":
    email_input = input("Enter email content: ")

    state = {
        "email": email_input
    }

    state = triage_email(state)
    print("🔍 Triage Decision:", state["decision"])

    state = react_loop(state)
