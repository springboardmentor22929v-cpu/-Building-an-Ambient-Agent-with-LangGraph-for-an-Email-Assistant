import json
from triage import triage_email

# 1️⃣ Load extracted email from Gmail
with open("latest_email.json", "r", encoding="utf-8") as f:
    email_data = json.load(f)

email_text = f"""
From: {email_data.get("from")}
Subject: {email_data.get("subject")}

{email_data.get("body")}
"""

print("📧 EMAIL INPUT TO LLM")
print(email_text)
print("-" * 50)

# 2️⃣ Send email to Gemini (LLM) for triage
decision = triage_email(email_text)

print("🤖 LLM TRIAGE DECISION:", decision)

# 3️⃣ Store result in JSON
result = {
    "email": email_data,
    "triage_decision": decision
}

with open("triage_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4)

print("\n✅ Triage result saved to triage_result.json")