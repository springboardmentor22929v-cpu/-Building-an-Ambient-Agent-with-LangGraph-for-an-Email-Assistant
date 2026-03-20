import sys
import os
sys.path.append('.')  # Ensure local modules are found

from evaluate_triage import TriageEvaluator
from demo_agent import DemoEmailAgent
from golden_dataset import get_golden_emails
import json

# -----------------------------
# Initialize evaluator
# -----------------------------
evaluator = TriageEvaluator()

# -----------------------------
# Run evaluation
# -----------------------------
print("✅ LangSmith CONNECTED")
print("📁 Project: Email-Assistant-project")
print("Starting evaluation...")

metrics = evaluator.run_evaluation()

# -----------------------------
# Save results manually to JSON
# -----------------------------
results_file = "triage_evaluation_results.json"
try:
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
    print(f"✅ Evaluation results saved to {results_file}")
except Exception as e:
    print(f"❌ Error saving results: {str(e)}")

# -----------------------------
# Print evaluation summary
# -----------------------------
print("\n📊 Detailed Results Summary:")
print(f"Total emails evaluated: {metrics.get('total_predictions', 0)}")
print(f"Correct predictions: {metrics.get('correct_predictions', 0)}")
accuracy = metrics.get('overall_accuracy', 0)
print(f"Accuracy: {accuracy:.2%}")

# Check if evaluation passes threshold
if accuracy >= 0.80:
    print("✅ SUCCESS: Evaluation passed!")
else:
    print("❌ FAILED: Evaluation did not meet 80% accuracy threshold")

# -----------------------------
# Display top errors (up to 5)
# -----------------------------
errors = [r for r in metrics.get('detailed_results', []) if not r.get('correct', False)]
if errors:
    print("\n⚠️ Top errors:")
    for error in errors[:5]:
        subject = error.get('subject', 'N/A')
        expected = error.get('expected', 'N/A')
        predicted = error.get('predicted', 'N/A')
        print(f"- {subject}: Expected '{expected}', Got '{predicted}'")
else:
    print("\n🎉 No errors found in top 5 emails.")
