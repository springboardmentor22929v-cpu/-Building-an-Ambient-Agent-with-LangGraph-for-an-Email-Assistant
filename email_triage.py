import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from state import EmailAgentState

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise ValueError("❌ GOOGLE_API_KEY not found in environment variables")

print("✅ Loaded Key:", google_api_key[:10] + "...")

# -----------------------------
# Initialize LLM
# -----------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",   # Updated to valid model name
    temperature=0,
    google_api_key=google_api_key
)

# -----------------------------
# Prompt template
# -----------------------------
triage_template = """
You are an expert email triage assistant.

Classify this email into exactly ONE category:

1. ignore — spam, newsletters, promotional emails, no action needed
2. notify_human — urgent issues, deadlines, sensitive topics
3. respond — any email where a helpful reply can be drafted

When in doubt → notify_human.

Respond ONLY in this format:
DECISION: [ignore/notify_human/respond]
REASONING: [one sentence]

EMAIL:
From: {email_from}
To: {email_to}
Subject: {email_subject}
Body: {email_body}
"""

triage_prompt = PromptTemplate(
    template=triage_template,
    input_variables=["email_from", "email_to", "email_subject", "email_body"]
)

# -----------------------------
# TRIAGE NODE
# -----------------------------
def triage_node(state: EmailAgentState) -> EmailAgentState:

    print(f"\n📨 TRIAGE: Processing email from {state.get('email_from')}")

    prompt_text = triage_prompt.format(
        email_from=state.get("email_from", ""),
        email_to=state.get("email_to", ""),
        email_subject=state.get("email_subject", ""),
        email_body=state.get("email_body", "")
    )

    response = llm.invoke(prompt_text)
    content = response.content

    decision = None
    reasoning = None

    for line in content.strip().split("\n"):
        if line.startswith("DECISION:"):
            decision = line.split(":", 1)[1].strip().lower()
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

    if decision not in ["ignore", "notify_human", "respond"]:
        print("⚠️ Invalid decision — defaulting to notify_human")
        decision = "notify_human"
        reasoning = "Failed to parse LLM response"

    print(f"✓ Decision: {decision}")
    print(f"Reasoning: {reasoning}")

    return {
        **state,
        "triage_decision": decision,
        "triage_reasoning": reasoning
    }

# -----------------------------
# TEST RUN
# -----------------------------
if __name__ == "__main__":

    test_state = {
        "email_from": "manager@company.com",
        "email_to": "anjalik150904@gmail.com",
        "email_subject": "Meeting tomorrow",
        "email_body": "Can we schedule a meeting tomorrow?"
    }

    result = triage_node(test_state)
    print("\nRESULT:", result)
