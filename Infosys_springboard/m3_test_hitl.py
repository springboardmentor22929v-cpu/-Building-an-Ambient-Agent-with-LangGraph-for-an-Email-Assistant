"""
Milestone 3: Test HITL (Human-in-the-Loop) Flow
Demonstrates interrupt and resume with approval.
"""

import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

load_dotenv()

from graph import app

print("=" * 80)
print("🧪 MILESTONE 3: TESTING HITL FLOW")
print("=" * 80)

# Test email that will trigger respond_act → dangerous tool
test_email = """
From: Project Guide <guide@college.edu>
Subject: Project Review Meeting

Hi Abinaya,

Can we schedule the project review meeting for Friday at 3 PM?

Please confirm.

Regards,
Guide
"""

config = RunnableConfig(
    configurable={"thread_id": "test_hitl_001"},
    tags=["milestone-3", "hitl-test"]
)

print("\n📧 Test Email:")
print(test_email)
print("-" * 80)

# ==================================================
# STEP 1: Initial run (will interrupt)
# ==================================================
print("\n1️⃣ RUNNING AGENT (will interrupt for approval)...")
print("-" * 80)

try:
    result = app.invoke(
        {"email": test_email},
        config=config
    )
    print("\n✅ Completed without interrupt (unexpected!)")
    print(result)
    
except Exception as e:
    # Check if it's an interrupt
    error_msg = str(e)
    if "interrupt" in error_msg.lower():
        print("\n⛔ INTERRUPT TRIGGERED!")
        print(f"   Message: {error_msg}")
        print("\n✅ This is CORRECT behavior for Milestone 3!")
    else:
        print(f"\n❌ Unexpected error: {e}")
        raise

# ==================================================
# STEP 2: Get current state
# ==================================================
print("\n2️⃣ CHECKING INTERRUPTED STATE...")
print("-" * 80)

state = app.get_state(config)
print(f"\n📊 Current State:")
print(f"   Next node: {state.next}")
print(f"   State values: {state.values}")

# ==================================================
# STEP 3: Simulate human approval
# ==================================================
print("\n3️⃣ SIMULATING HUMAN APPROVAL...")
print("-" * 80)

# Update state with human decision
app.update_state(
    config,
    {"human_decision": "approve"},
    as_node="human_decision"
)

print("✅ Human approved the action")

# ==================================================
# STEP 4: Resume execution
# ==================================================
print("\n4️⃣ RESUMING EXECUTION...")
print("-" * 80)

# Resume from where it stopped
result = app.invoke(None, config=config)

print("\n✅ EXECUTION COMPLETED!")
print("\n📊 Final Result:")
print(result)

# ==================================================
# Summary
# ==================================================
print("\n" + "=" * 80)
print("🎉 MILESTONE 3 HITL TEST COMPLETE!")
print("=" * 80)
print("\n✅ Successfully demonstrated:")
print("   1. Interrupt on dangerous tool")
print("   2. State preservation")
print("   3. Human approval")
print("   4. Resume execution")
print("\n💡 Next: Run this in LangGraph Studio to see the inbox UI!")
print("=" * 80)