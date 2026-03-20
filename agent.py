# agent.py
import os
import json
from dotenv import load_dotenv

from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from golden_dataset import GOLDEN_EMAILS  # Your golden email list

# ---------------- Load Environment ----------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print("Loaded API key:", GOOGLE_API_KEY is not None)

# ---------------- LangSmith Client ----------------
client = Client()

# ---------------- Gemini Models ----------------
agent_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    temperature=0.3,
    api_key=GOOGLE_API_KEY
)

judge_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    api_key=GOOGLE_API_KEY
)

# ---------------- Prompt ----------------
prompt = PromptTemplate(
    input_variables=["email"],
    template="""
You are an email assistant.
Draft a polite, professional, and helpful reply to the following email:

Email:
{email}
"""
)

# ---------------- Agent ----------------
def run_agent(email: str):
    """Run the email assistant on a single email"""
    chain = LLMChain(llm=agent_llm, prompt=prompt)
    result = chain.run({"email": email})
    return result

# ---------------- LLM-as-a-Judge ----------------
def quality_evaluator(run, example):
    """Evaluate a single agent response"""
    eval_prompt = f"""
You are an evaluator for an email assistant.

Evaluate the agent reply on a scale of 0-10:

1. Politeness
2. Correct identification of key date/time
3. Professional tone
4. Helpfulness

User Email:
{example.inputs["email"]}

Agent Reply:
{run.outputs["output"]}

Return ONLY JSON:
{{ "politeness": 0, "accuracy": 0, "tone": 0, "helpfulness": 0 }}
"""
    result = judge_llm.invoke(eval_prompt)
    return {"Agent_Quality_Score": json.loads(result.content)}

# ---------------- Prepare Golden Dataset ----------------
def prepare_dataset():
    """Convert GOLDEN_EMAILS into LangSmith format"""
    dataset = []
    for email in GOLDEN_EMAILS:
        full_email = f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['content']}"
        dataset.append({
            "inputs": {"email": full_email},
            "outputs": {"output": email.get("expected_response", "")}
        })
    return dataset

# ---------------- Get or Create Dataset ----------------
def get_or_create_dataset(client, dataset_name, dataset_description):
    """Fetch existing dataset or create a new one"""
    try:
        datasets = client.list_datasets()
        for ds in datasets:
            if ds.name == dataset_name:
                print(f"Using existing dataset: {dataset_name}")
                return ds
    except Exception as e:
        print(f"Error listing datasets: {e}")

    # Create new dataset
    print(f"Creating new dataset: {dataset_name}")
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description=dataset_description
    )

    # Upload examples
    examples = prepare_dataset()
    for example in examples:
        client.create_example(
            inputs=example["inputs"],
            outputs=example["outputs"],
            dataset_id=dataset.id
        )

    print(f"Created dataset with {len(examples)} examples")
    return dataset

# ---------------- Main ----------------
if __name__ == "__main__":
    print("Dataset size:", len(GOLDEN_EMAILS))

    # Get or create dataset
    dataset = get_or_create_dataset(
        client,
        dataset_name="golden-emails-dataset",
        dataset_description="Golden dataset for email assistant evaluation"
    )

    # Fetch dataset examples (needed for evaluate)
    examples = list(client.list_examples(dataset.id))

    # Run evaluation
    evaluate(
        run_agent,
        data=examples,
        evaluators=[quality_evaluator],
        experiment_prefix="week4-gemini-quality-eval",
        client=client
    )