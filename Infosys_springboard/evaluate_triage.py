import json
import os
import time
from triage import triage_email
from evaluation_data import golden_set

RESULTS_FILE = "results.json"

# 1️⃣ Load old results if file exists
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, "r") as f:
        results = json.load(f)
else:
    results = []

already_tested = len(results)
correct = sum(1 for r in results if r["correct"])

print(f"🔁 Resuming from sample {already_tested + 1}")

# 2️⃣ Run remaining samples
for i in range(already_tested, len(golden_set)):
    email_obj = golden_set[i]["email"]
    true_label = golden_set[i]["label"]

    # Convert email JSON → readable text
    email_text = (
        f"From: {email_obj['from']}\n"
        f"Subject: {email_obj['subject']}\n\n"
        f"{email_obj['body']}"
    )

    try:
        predicted_label = triage_email(email_text)
    except Exception as e:
        print("❌ Error:", e)
        print("⏸️ Stop now. Resume later.")
        break

    is_correct = predicted_label == true_label
    if is_correct:
        correct += 1

    results.append({
        "from": email_obj["from"],
        "subject": email_obj["subject"],
        "true": true_label,
        "predicted": predicted_label,
        "correct": is_correct
    })

    print(f"[{i+1}/{len(golden_set)}]")
    print("Subject:", email_obj["subject"])
    print("True:", true_label)
    print("Predicted:", predicted_label)
    print("Correct:", is_correct)
    print("-" * 60)

    time.sleep(6)  # ⭐ VERY IMPORTANT for free-tier

# 3️⃣ Save results
with open(RESULTS_FILE, "w") as f:
    json.dump(results, f, indent=2)

accuracy = (correct / len(results)) * 100

print("\n✅ FINAL EVALUATION STATUS")
print(f"Tested so far: {len(results)}")
print(f"Correct predictions: {correct}")
print(f"Accuracy: {accuracy:.2f}%")
print("📁 Results saved to results.json")