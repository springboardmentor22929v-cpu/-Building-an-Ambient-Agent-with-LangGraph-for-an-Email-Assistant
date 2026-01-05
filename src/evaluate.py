import json
from agent import build_graph
from langsmith import Client

# Initialize LangSmith client
client = Client()

# Load dataset
with open("data/test_emails.json") as f:
    emails = json.load(f)

app = build_graph()

correct = 0
results = []

for email in emails:
    state = {"email": email, "trace": []}  # add trace list
    final_state = app.invoke(state)

    predicted = final_state["triage"]
    expected = email["label"]
    is_correct = predicted == expected
    correct += int(is_correct)

    results.append({
        "subject": email["subject"],
        "expected": expected,
        "predicted": predicted,
        "correct": is_correct
    })

# ✅ Step 4: Send run to LangSmith
client.create_run(
    name="Milestone1 Evaluation",
    inputs=email,
    outputs=final_state,
    run_type="chain",   # <-- required argument
    project="Email Assistant Milestone 1"
)

# Print results
for r in results:
    print(f"Subject: {r['subject']}")
    print(f"Expected: {r['expected']} | Predicted: {r['predicted']} | Correct: {r['correct']}")
    print("---")

accuracy = correct / len(emails)
print(f"\nFinal Accuracy: {accuracy:.2%}")