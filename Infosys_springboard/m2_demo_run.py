# m2_demo_run.py
import os
from dotenv import load_dotenv

from langchain_core.runnables import RunnableConfig
from m2_langsmith_force_tracer import get_tracer
import time

# =================================================
# 1️⃣ Load env & force tracing FIRST
# =================================================
load_dotenv(override=True)

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "email-triage-m2"

# ✅ ADD DEBUG OUTPUT RIGHT HERE (Line 18-25)
print("=" * 60)
print("🔍 DEBUG: Environment Variables Check")
print("=" * 60)
print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")
print(f"LANGCHAIN_API_KEY exists: {bool(os.getenv('LANGCHAIN_API_KEY'))}")
print(f"LANGCHAIN_API_KEY first 10 chars: {os.getenv('LANGCHAIN_API_KEY', '')[:10]}...")
print(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
print("=" * 60)

assert os.getenv("LANGCHAIN_API_KEY"), "❌ LANGCHAIN_API_KEY not set"

print("✅ LangSmith tracing enabled")
print("✅ Project:", os.environ["LANGCHAIN_PROJECT"])

# =================================================
# 2️⃣ Create LangSmith tracer (THIS WAS MISSING)
# =================================================
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from langchain_core.runnables import RunnableConfig

# ✅ ADD CONNECTION TEST RIGHT HERE (Line 43-55)
print("\n🔍 Testing LangSmith connection...")
try:
    client = Client()
    projects = list(client.list_projects(limit=1))
    print(f"✅ LangSmith connection successful")
    print(f"✅ Found {len(projects)} project(s)")
    for p in projects[:1]:
        print(f"   - {p.name} (ID: {p.id[:8]}...)")
except Exception as e:
    print(f"❌ LangSmith connection failed: {e}")
    # Don't exit, just warn

tracer = LangChainTracer(
    project_name=os.environ["LANGCHAIN_PROJECT"],
    client=client
)

print("✅ LangSmith tracer attached")

# =================================================
# 3️⃣ Import graph AFTER tracer setup
# =================================================
from graph import app

# =================================================
# 4️⃣ Demo email
# =================================================
email_text = """
From: Project Guide <guide@college.edu>
Subject: Project Review Meeting

Hi Abinaya,

Can we schedule the project review meeting for Friday at 3 PM?

Please confirm.

Regards,
Guide
"""

print("\n📧 INPUT EMAIL")
print(email_text)
print("=" * 60)

# =================================================
# 5️⃣ Run agent WITH tracer callback
# =================================================
tracer = get_tracer()

# ✅ ADD TRACER DEBUG RIGHT HERE (Line 94-95)
print(f"\n🔍 Using tracer type: {type(tracer).__name__}")
print(f"🔍 Tracer project: {tracer.project_name}")

result = app.invoke(
    {"email": email_text},
    config=RunnableConfig(
        configurable={"thread_id": "demo-001"},
        callbacks=[tracer],   # 🔥 THIS IS THE KEY LINE
        tags=["demo", "milestone-2"],
        metadata={
            "source": "m2_demo_run",
            "purpose": "show tracing"
        }
    )
)

# ✅ ADD UPLOAD STATUS RIGHT HERE (Line 115-121)
print("\n🔄 Waiting for trace upload to LangSmith...")
for i in range(5):
    time.sleep(1)
    print(f"   Waited {i+1}s...")
print("✅ Upload wait complete")

print("\n🤖 FINAL AGENT OUTPUT")
print(result)
print("=" * 60)

# ✅ ADD FINAL CHECK RIGHT HERE (Line 130-140)
print("\n🔍 Checking for traces in LangSmith...")
try:
    # Small delay to ensure upload
    time.sleep(2)
    runs = list(client.list_runs(project_name=os.environ["LANGCHAIN_PROJECT"], limit=3))
    print(f"✅ Found {len(runs)} run(s) in project '{os.environ['LANGCHAIN_PROJECT']}'")
    for i, run in enumerate(runs[:3]):
        print(f"   {i+1}. {run.name} | {run.status} | {run.start_time.strftime('%H:%M:%S')}")
except Exception as e:
    print(f"⚠️  Could not verify runs: {e}")

print("✅ Demo run complete")