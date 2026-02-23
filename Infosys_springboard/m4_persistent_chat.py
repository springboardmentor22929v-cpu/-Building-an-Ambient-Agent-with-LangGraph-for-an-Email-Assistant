import sqlite3
import time
from langgraph.checkpoint.sqlite import SqliteSaver
from m4_graph import builder
from m4_memory import init_memory, get_all_preferences

def run_persistent_chat():
    print("\n🧠 Persistent M4 Agent (I Remember Everything!)")
    print("==============================================")
    
    # 1. Initialize Memory (Does NOT clear old data)
    init_memory()
    
    # 2. Configure graph with checkpointer
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)
    
    app = builder.compile(
        checkpointer=memory,
        interrupt_before=["human_decision"]
    )
    
    config = {"configurable": {"thread_id": "persistent_chat_001"}}
    
    # 3. Show current memory
    start_prefs = get_all_preferences()
    print(f"📝 Current Memory: {start_prefs}")
    
    # 4. Input Loop
    while True:
        print("\n----------------------------------------------")
        print("Enter email details (or typed 'exit' to quit):")
        recipient = input("To (Name): ").strip()
        if recipient.lower() == 'exit': break
        
        body_input = input("Instructions: ").strip()
        
        inputs = {
            "sender": "Me <me@company.com>",
            "subject": "Task",
            "body": f"Email {recipient}: {body_input}"
        }
        
        print("\n🤖 Thinking...")
        
        # Run until interruption (Human Review)
        for event in app.stream(inputs, config):
            for key, value in event.items():
                if key == "triage":
                    draft = value.get("generated_body", "")
                    print(f"\n📄 Draft:\n{draft}\n")

        # Check for pause
        snapshot = app.get_state(config)
        if snapshot.next:
            print("⏸️  Review needed. Type 'approve' to send, or type your CORRECTION:")
            user_response = input("Decision/Edit: ").strip()
            
            if user_response.lower() == "approve":
                # User approved logic
                app.update_state(config, {"human_decision": "approve"}, as_node="hitl_checkpoint")
            else:
                # User edited logic
                print("✏️  Updating draft with your correction...")
                app.update_state(config, {
                    "generated_body": user_response,
                    "human_decision": "approve" 
                }, as_node="hitl_checkpoint")
            
            # Resume
            print("▶️  Resuming...")
            for event in app.stream(None, config):
                 pass # let it finish
                 
            # 5. Show Updated Memory
            new_prefs = get_all_preferences()
            print(f"\n🧠 Updated Memory: {new_prefs}")

if __name__ == "__main__":
    run_persistent_chat()
