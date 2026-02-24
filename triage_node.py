from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from state import AgentState


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    convert_system_message_to_human=True
)

triage_template = """
You are an expert email triage assistant.

MEMORY CONTEXT:
{memory_context}

Classify this email into exactly ONE category:

1. ignore → Spam, newsletters, irrelevant
2. notify_human → Critical alerts, deadlines, important FYI
3. respond → Any email where drafting acknowledgment or reply is helpful

Email:
From: {email_from}
Subject: {email_subject}
Body: {email_body}

Respond in EXACT format:
DECISION: <ignore/notify_human/respond>
REASONING: <one short explanation>
"""

triage_prompt = PromptTemplate(
    template=triage_template,
    input_variables=["email_from", "email_subject", "email_body", "memory_context"]
)


def triage_node(state: AgentState) -> AgentState:
    print("\n📋 Running Triage")

    user_memory = state.get("user_preferences", {})
    sender_email = state.get("email_from")
    email_subject = state.get("email_subject", "")
    email_body = state.get("email_body", "")

    sender_context = user_memory.get("sender_context")
    corrections = user_memory.get("triage_corrections", [])
    past_feedback = user_memory.get("past_feedback", [])
    preferences = user_memory.get("preferences", {})

    # =====================================================
    # 1️⃣ Sender-Level Hard Override (Always apply)
    # =====================================================
    if sender_context and sender_context.get("triage_override"):
        override = sender_context["triage_override"]

        print(f"⚡ TRIAGE OVERRIDE from sender context: {override}")

        return {
            **state,
            "triage_decision": override,
            "triage_reasoning": f"Memory override applied for sender {sender_email}"
        }

    # =====================================================
    # 2️⃣ SOFT Learning – Require Multiple Corrections
    # =====================================================
    matching_corrections = [
        c for c in corrections
        if c.get("email_from") == sender_email
        and c.get("email_subject") == email_subject
    ]

    if len(matching_corrections) >= 2:
        corrected_decision = matching_corrections[-1].get("corrected_decision")

        print(f"🧠 Applying learned correction (confidence ≥ 2): {corrected_decision}")

        return {
            **state,
            "triage_decision": corrected_decision,
            "triage_reasoning": "Applied learned correction after repeated pattern"
        }

    # =====================================================
    # 3️⃣ Build Smart Memory Context for LLM
    # =====================================================
    memory_parts = []

    if preferences:
        memory_parts.append(f"User Preferences: {preferences}")

    if corrections:
        memory_parts.append(
            f"Past corrections count: {len(corrections)}"
        )

    if past_feedback:
        memory_parts.append("User frequently edits drafts for tone/clarity.")

    memory_context = "\n".join(memory_parts) if memory_parts else "No prior memory."

    # =====================================================
    # 4️⃣ LLM Classification
    # =====================================================
    prompt_text = triage_prompt.format(
        email_from=sender_email,
        email_subject=email_subject,
        email_body=email_body,
        memory_context=memory_context
    )

    response = llm.invoke(prompt_text)
    content = response.content

    decision = None
    reasoning = None

    for line in content.strip().split("\n"):
        if "DECISION:" in line:
            decision = line.split(":", 1)[1].strip().lower()
        elif "REASONING:" in line:
            reasoning = line.split(":", 1)[1].strip()

    # =====================================================
    # 5️⃣ Safety Fallback
    # =====================================================
    if decision not in ["ignore", "notify_human", "respond"]:
        print("⚠️ Invalid triage decision, defaulting to respond")
        decision = "respond"
        reasoning = "Fallback decision to respond helpfully."

    print(f"📋 TRIAGE DECISION: {decision.upper()}")

    return {
        **state,
        "triage_decision": decision,
        "triage_reasoning": reasoning
    }
