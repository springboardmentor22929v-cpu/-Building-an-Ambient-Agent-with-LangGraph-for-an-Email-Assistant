import os
import json
import time
from typing import Dict, List

# -------- Load Environment Variables --------
from dotenv import load_dotenv
load_dotenv(override=True)

# -------- LangSmith Tracing --------
from langsmith import traceable

# -------- Gemini Error Handling --------
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

# -------- Your Project Imports --------
from email_triage import triage_node
from golden_dataset import get_golden_emails


# -------- Environment Check --------
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "Email-Assistant-project")

if LANGCHAIN_API_KEY:
    print("✅ LangSmith CONNECTED")
    print(f"📁 Project: {LANGCHAIN_PROJECT}")
else:
    print("❌ LANGCHAIN_API_KEY missing — tracing disabled")


# -------- Evaluator Configuration --------
MAX_EVAL_SAMPLES = 20
REQUEST_DELAY = 13   # Gemini free-tier allows 5 requests per minute


# -------- Evaluator Class --------
class TriageEvaluator:
    def __init__(self):
        pass

    @traceable(name="email-triage-single")
    def evaluate_single_email(self, email_data: Dict) -> Dict:
        """
        Evaluate one email using LLM-based triage.
        Automatically retries if rate limit is hit.
        """
        state = {
            "email_from": email_data["sender"],
            "email_to": "user@company.com",
            "email_subject": email_data["subject"],
            "email_body": email_data["content"]
        }

        retry_attempts = 2

        for attempt in range(retry_attempts):
            try:
                result = triage_node(state)
                break

            except ChatGoogleGenerativeAIError as e:
                if "RESOURCE_EXHAUSTED" in str(e):
                    print("⚠️ Rate limit hit. Waiting 15 seconds before retry...")
                    time.sleep(15)
                else:
                    raise e
        else:
            print("❌ Failed after retries.")
            result = {"triage_decision": "error"}

        predicted = result.get("triage_decision")
        expected = email_data.get("expected_triage")

        return {
            "sender": email_data["sender"],
            "subject": email_data["subject"],
            "expected": expected,
            "predicted": predicted,
            "correct": predicted == expected,
        }

    @traceable(name="email-triage-evaluation")
    def run_evaluation(self) -> Dict:
        """
        Run evaluation over a subset of the golden dataset
        """
        dataset: List[Dict] = get_golden_emails()[:MAX_EVAL_SAMPLES]
        results = []

        for idx, email in enumerate(dataset):
            print(f"\n🔎 Evaluating {idx + 1}/{len(dataset)}")
            results.append(self.evaluate_single_email(email))

            # Avoid free-tier rate limit
            if idx < len(dataset) - 1:
                print(f"⏳ Waiting {REQUEST_DELAY} seconds to avoid rate limit...")
                time.sleep(REQUEST_DELAY)

        correct = sum(1 for r in results if r["correct"])
        total = len(results)

        return {
            "overall_accuracy": correct / total if total else 0,
            "correct_predictions": correct,
            "total_predictions": total,
            "results": results,
        }


# -------- Main Runner --------
def main():
    evaluator = TriageEvaluator()
    metrics = evaluator.run_evaluation()

    print("\n📊 FINAL RESULT")
    print(f"Accuracy: {metrics['overall_accuracy']:.2%}")
    print(f"Correct: {metrics['correct_predictions']} / {metrics['total_predictions']}")

    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("💾 Results saved to evaluation_results.json")
    print("🔗 View traces at https://smith.langchain.com/")


if __name__ == "__main__":
    main()