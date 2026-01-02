from dotenv import load_dotenv
load_dotenv()

from src.agents.email_graph import create_email_agent
import json

# Load test data
with open("data/sample_emails.json") as f:
    test_emails = json.load(f)

# Create agent
agent = create_email_agent()

# Test each email
print("\n" + "="*60)
print("TESTING TRIAGE AGENT")
print("="*60)

results = []

for email in test_emails:
    print(f"\n{'='*60}")
    print(f"Email #{email['id']}")
    print(f"From: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"Expected: {email['expected_triage']}")
    print(f"{'='*60}")
    
    # Run agent
    result = agent.invoke({
        "email_id": email["id"],
        "email_from": email["from"],
        "email_subject": email["subject"],
        "email_body": email["body"],
        "user_preferences": {}
    })
    
    # Check accuracy
    predicted = result["triage_decision"]
    expected = email["expected_triage"]
    correct = predicted == expected
    
    results.append({
        "email_id": email["id"],
        "expected": expected,
        "predicted": predicted,
        "correct": correct
    })
    
    print(f"\n{'✓' if correct else '✗'} Result: {predicted} (Expected: {expected})")

# Calculate accuracy
accuracy = sum(r["correct"] for r in results) / len(results)
print(f"\n{'='*60}")
print(f"ACCURACY: {accuracy:.1%} ({sum(r['correct'] for r in results)}/{len(results)})")
print(f"{'='*60}")