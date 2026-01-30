# test_batch.py

import os
import time
import io
import contextlib

# ==========================================
# 1. SAFETY LOCK (Crucial)
# ==========================================
# We FORCE the system to use Mock tools. 
# This overrides whatever is in your .env file.
os.environ["USE_REAL_TOOLS"] = "false"

# Import the Agent AFTER setting the environment variable
from data.test_samples import dataset
from core.agent import agent_engine

# Configuration
BATCH_SIZE = 5
RATE_LIMIT_DELAY = 60  # Seconds to wait between batches

def run_batch_test():
    total_emails = len(dataset)
    print(f"🚀 STARTING BATCH TEST ({total_emails} Scenarios)")
    print("🔒 MODE: SAFE (Mock Tools Active)")
    print("="*60)

    # Loop through data in chunks of 5
    for batch_start in range(0, total_emails, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_emails)
        current_batch = dataset[batch_start : batch_end]
        
        print(f"\n📦 Processing Batch (Items {batch_start + 1} to {batch_end})...")

        for i, email_text in enumerate(current_batch):
            global_idx = batch_start + i + 1
            print(f"\n📧 CASE #{global_idx}: Analyzing...")
            
            # Print a snippet of the input so you know what we are testing
            clean_input = email_text.strip().split('|')[1][:50] if "|" in email_text else email_text[:50]
            print(f"📝 Input: {clean_input}...")

            # Prepare the prompt
            prompt = f"INCOMING EMAIL DATA:\n{email_text}"
            
            # --- CAPTURE OUTPUT ---
            # We hide the "MOCK EMAIL SENT" prints initially so we can format them nicely later.
            captured_output = io.StringIO()
            
            try:
                with contextlib.redirect_stdout(captured_output):
                    # Invoke the Agent!
                    result = agent_engine.invoke(
                        {"messages": [("user", prompt)]},
                        {"recursion_limit": 10} # Prevent infinite loops
                    )
                
                # Retrieve the decision from Memory (state.py)
                decision = result.get("triage_decision", "UNKNOWN")
                tool_logs = captured_output.getvalue()

                # --- PRINT REPORT CARD ---
                if decision == "RESPOND":
                    print("🏷️  Category: [RESPOND] ✅")
                    
                    # Check if an email was actually drafted/sent
                    if "MOCK EMAIL SENT" in tool_logs:
                        print("\n📨 ACTION TAKEN (Mock):")
                        print(tool_logs.strip())
                    else:
                        print("⚠️ Decision was RESPOND, but no email tool was used.")
                        
                elif decision == "IGNORE":
                    print("🏷️  Category: [IGNORE] 🚫")
                    print("(Skipping email as expected)")
                    
                elif decision == "NOTIFY":
                    print("🔔 Category: [NOTIFY HUMAN] ⚠️")
                    print("(Escalated to human operator)")
                    
                else:
                    print(f"⚠️ Unknown Decision: {decision}")

            except Exception as e:
                print(f"❌ CRASHED: {e}")

            print("-" * 60)

        # Rate Limit Pause
        if batch_end < total_emails:
            print(f"⏳ Batch complete. Cooling down for {RATE_LIMIT_DELAY} seconds...")
            time.sleep(RATE_LIMIT_DELAY)
            print("▶️ Resuming...")

    print("\n✅ ALL TESTS COMPLETED.")

if __name__ == "__main__":
    run_batch_test()