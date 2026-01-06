def react_loop(state):
    decision = state["decision"]

    if decision == "respond_or_act":
        print("🤖 Agent reasoning: This email requires a response or action.")
        print("🛠 Using safe mock tool: draft_reply")
    else:
        print(f"📩 Decision: {decision}")

    return state
