import os
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from golden_dataset import get_golden_emails  # your dataset function

# ---------------- Load Environment ----------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# ---------------- LangSmith Client ----------------
client = Client()

# ---------------- Gemini Models ----------------
agent_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.3,
    api_key=GOOGLE_API_KEY
)

judge_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    api_key=GOOGLE_API_KEY
)

# ---------------- Prompt Template ----------------
prompt = PromptTemplate(
    input_variables=["email"],
    template="""
You are an email assistant.
Draft a polite, professional, and helpful reply to the following email:

Email:
{email}
"""
)

# ---------------- Agent Function ----------------
def run_agent(email: str):
    """Runs the agent LLM to produce an email reply."""
    chain = prompt | agent_llm
    result = chain.invoke({"email": email})
    return result.content

# ---------------- LLM-as-Judge Evaluator ----------------
def quality_evaluator(run, example):
    """
    Evaluates an agent's response using a judge LLM.
    Returns a JSON score for politeness, accuracy, tone, and helpfulness.
    """
    eval_prompt = f"""
You are an evaluator for an email assistant.

Evaluate the agent reply on:
1. Politeness (0-10)
2. Correct identification of key date/time (0-10)
3. Professional tone (0-10)
4. Helpfulness (0-10)

User Email:
{example.inputs["email"]}

Agent Reply:
{run.outputs["output"]}

Return ONLY JSON in this format:
{{
  "politeness": 0,
  "accuracy": 0,
  "tone": 0,
  "helpfulness": 0
}}
"""
    result = judge_llm.invoke(eval_prompt)
    return {"Agent_Quality_Score": result.content}

# ---------------- Run Evaluation ----------------
if __name__ == "__main__":
    print("✅ LangSmith CONNECTED")
    print("📁 Project: Email-Assistant-project")
    print("Starting evaluation...")

    # Load dataset
    data = get_golden_emails()  # should return list of dicts like [{"email": "..."}, ...]

    # Note: target is a positional-only argument in langsmith evaluate
    metrics = evaluate(
        run_agent,                 # agent function (positional argument)
        data=data,                 # dataset for evaluation
        evaluators=[quality_evaluator],
        client=client
    )

    # ---------------- Summary ----------------
    print("\n📊 Evaluation Summary")
    total = len(metrics)
    if total > 0:
        avg_politeness = sum(float(m["Agent_Quality_Score"].get("politeness", 0)) for m in metrics) / total
        avg_accuracy = sum(float(m["Agent_Quality_Score"].get("accuracy", 0)) for m in metrics) / total
        avg_tone = sum(float(m["Agent_Quality_Score"].get("tone", 0)) for m in metrics) / total
        avg_helpfulness = sum(float(m["Agent_Quality_Score"].get("helpfulness", 0)) for m in metrics) / total

        print(f"Total emails evaluated: {total}")
        print(f"Average Politeness: {avg_politeness:.2f}/10")
        print(f"Average Accuracy: {avg_accuracy:.2f}/10")
        print(f"Average Tone: {avg_tone:.2f}/10")
        print(f"Average Helpfulness: {avg_helpfulness:.2f}/10")
    else:
        print("No evaluation results returned.")
