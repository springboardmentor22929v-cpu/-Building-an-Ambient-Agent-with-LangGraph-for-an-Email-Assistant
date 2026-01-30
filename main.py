# main.py
import os
import sys
import time
from dotenv import load_dotenv
from core.agent import agent_engine
from tools.fetch_tool import fetch_unread_emails
from langchain_core.messages import AIMessage

# Load Environment Variables
load_dotenv()

def run_manager_mode():
    print("🚀 AMBIENT AGENT: MANAGER MODE (Stable Version)")
    print("="*60)

    config = {"configurable": {"thread_id": "1"}}

    try:
        # 1. FETCH EMAILS
        print(f"👀 Checking Inbox...")
        inbox_status = fetch_unread_emails.invoke({})

        if "No new unread emails" in inbox_status:
            print("💤 Status: No new mail found.")
            return

        print("⚡ NEW MAIL DETECTED! Analyzing...")
        print("-" * 60)
        
        prompt = f"INCOMING EMAIL DATA:\n{inbox_status}"
        
        # 2. START AGENT
        # We run the first step (Triage -> Draft/Calendar)
        agent_engine.invoke({"messages": [("user", prompt)]}, config)

        # 3. SMART LOOP (Max 3 turns to prevent infinite loops)
        for turn in range(3):
            # Get the current state (Where is the agent?)
            snapshot = agent_engine.get_state(config)
            
            # If agent finished, we are done.
            if not snapshot.next:
                decision = snapshot.values.get("triage_decision", "UNKNOWN")
                print(f"🤖 FINAL DECISION: {decision}")
                return

            # Get the pending tool call
            last_msg = snapshot.values["messages"][-1]
            if not last_msg.tool_calls:
                print("⚠️ Agent paused but no tool call found. Resuming...")
                agent_engine.invoke(None, config)
                continue

            tool_call = last_msg.tool_calls[0]
            tool_name = tool_call["name"]
            args = tool_call["args"]

            # --- CASE 1: CHECK CALENDAR (Auto-Run) ---
            if tool_name == "check_calendar":
                print(f"\n📅 ACTION: Checking Calendar...")
                # Run the tool and let the agent continue thinking
                agent_engine.invoke(None, config) 
                print("   ✅ Calendar Checked. Agent is thinking about the reply...")
                continue # Go to next turn (which should be the email draft)

            # --- CASE 2: WRITE EMAIL (The HITL Menu) ---
            elif tool_name == "write_email":
                cur_to = args.get('to')
                cur_sub = args.get('subject')
                cur_body = args.get('content') or args.get('body')

                print(f"\n✋ PENDING EMAIL ACTION:")
                print(f"   To:      {cur_to}")
                print(f"   Subject: {cur_sub}")
                print(f"   Body:    {cur_body}")
                print("-" * 60)

                print("[A]pprove : Send immediately.")
                print("[E]dit    : Modify details.")
                print("[R]eject  : Cancel.")
                choice = input("\n👉 Action (A/E/R): ").strip().upper()

                if choice == "A":
                    print("\n✅ APPROVED. Sending...")
                    final = agent_engine.invoke(None, config)
                    print("📨 TOOL OUTPUT:", final["messages"][-1].content)
                    return # DONE

                elif choice == "E":
                    print("\n📝 EDIT MODE")
                    new_sub = input(f"Subject [{cur_sub}]: ").strip() or cur_sub
                    new_body = input(f"Body    [{cur_body}]: ").strip() or cur_body
                    
                    new_tool_call = tool_call.copy()
                    new_tool_call["args"] = {"to": cur_to, "subject": new_sub, "content": new_body}
                    
                    new_msg = AIMessage(content=last_msg.content, tool_calls=[new_tool_call], id=last_msg.id)
                    agent_engine.update_state(config, {"messages": [new_msg]})
                    
                    print("\n✅ DRAFT UPDATED. Sending...")
                    final = agent_engine.invoke(None, config)
                    print("📨 TOOL OUTPUT:", final["messages"][-1].content)
                    return # DONE

                else:
                    print("❌ REJECTED. Action cancelled.")
                    return # DONE

            # --- CASE 3: UNKNOWN TOOL ---
            else:
                print(f"⚠️ Unknown Tool: {tool_name}. Auto-Approving...")
                agent_engine.invoke(None, config)
                continue

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {e}")

if __name__ == "__main__":
    if os.getenv("USE_REAL_TOOLS") != "true":
        print("⚠️  WARNING: You are in MOCK MODE.")
    run_manager_mode()