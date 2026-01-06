from app.llm.gemini import llm

def triage_email(state):
    email = state["email"]

    prompt = f"""
    Classify the email into one category:
    - ignore
    - notify_human
    - respond_or_act

    Email:
    {email}

    Output only the category name.
    """

    decision = llm.invoke(prompt).content.strip().lower()

    return {
        "email": email,
        "decision": decision
    }
