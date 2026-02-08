# m3_demo_run.py
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from graph import app

# Load env
load_dotenv(override=True)

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "email-triage-m2"

email_text = """
From: Project Guide <guide@college.edu>
Subject: Project Review Meeting

Can we schedule the project review meeting for Friday at 3 PM?
"""

print("📧 INPUT EMAIL:")
print(email_text)
print("=" * 60)

try:
    result = app.invoke(
        {"email": email_text},
        config=RunnableConfig(
            configurable={"thread_id": "m3-demo-001"},
            tags=["milestone-3", "hitl"],
            metadata={"purpose": "HITL demo"}
        )
    )
    print("🤖 OUTPUT:", result)

except Exception as e:
    print("⏸️ EXECUTION PAUSED (EXPECTED)")
    print(e)
