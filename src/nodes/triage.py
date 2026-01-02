from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from src.agents.state import EmailAgentState

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# Single prompt template 
triage_template = """You are an expert email triage assistant.

Your job is to classify incoming emails into exactly ONE of these categories:

1. **ignore**: 
   - Newsletters, promotional emails, automated notifications
   - Spam, advertisements
   - Emails that require no action

2. **notify_human**: 
   - Urgent issues requiring immediate human attention
   - Sensitive topics (HR, legal, personal issues)
   - Emails from VIPs (CEO, important clients)
   - Unclear requests that need human judgment

3. **respond**: 
   - Clear, actionable requests you can help with
   - Meeting requests, information queries
   - Emails where you can draft a helpful reply
   - Follow-ups on ongoing conversations

Rules:
- When in doubt between notify_human and respond, choose notify_human
- Be conservative: better to notify human than ignore something important
- Consider the sender's importance

Respond in this exact format:
DECISION: [ignore/notify_human/respond]
REASONING: [1-2 sentence explanation]

---

Now classify this email:

From: {email_from}
Subject: {email_subject}
Body: {email_body}

Your classification:"""

triage_prompt = PromptTemplate(
    template=triage_template,
    input_variables=["email_from", "email_subject", "email_body"]
)

def triage_node(state: EmailAgentState) -> EmailAgentState:
    """
    Classifies an incoming email into ignore, notify_human, or respond.
    """
    print(f"\n🔍 TRIAGE: Processing email from {state['email_from']}")
    
    # Create the full prompt
    prompt_text = triage_prompt.format(
        email_from=state["email_from"],
        email_subject=state["email_subject"],
        email_body=state["email_body"]
    )
    
    # Invoke LLM
    response = llm.invoke(prompt_text)
    
    # Parse response
    content = response.content
    lines = content.strip().split('\n')
    
    decision = None
    reasoning = None
    
    for line in lines:
        if "DECISION:" in line:
            decision = line.split(":", 1)[1].strip().lower()
        elif "REASONING:" in line:
            reasoning = line.split(":", 1)[1].strip()
    
    # Validate decision
    if decision not in ["ignore", "notify_human", "respond"]:
        print(f"⚠️ Invalid decision '{decision}', defaulting to notify_human")
        decision = "notify_human"
        reasoning = "Failed to parse LLM response"
    
    print(f"✓ Decision: {decision}")
    print(f"  Reasoning: {reasoning}")
    
    return {
        **state,
        "triage_decision": decision,
        "triage_reasoning": reasoning
    }