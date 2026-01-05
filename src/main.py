from agent import build_graph

emails = [
    {"subject": "Monthly Newsletter", "sender": "news@vendor.com", "body": "Unsubscribe here."},
    {"subject": "Urgent: Invoice Error", "sender": "accounts@partner.com", "body": "Please fix immediately."},
    {"subject": "Meeting request", "sender": "alex@company.com", "body": "Can we schedule next week?"},
]

app = build_graph()

for email in emails:
    state = {"email": email}
    result = app.invoke(state)
    print(f"\nEmail: {email['subject']}")
    print(f"Triage: {result['triage']}")
    print(f"Result: {result['result']}")