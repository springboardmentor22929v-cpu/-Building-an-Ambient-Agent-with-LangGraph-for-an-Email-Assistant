import sqlite3
import time
from langgraph.checkpoint.sqlite import SqliteSaver
from m4_graph import builder
from m4_memory import init_memory, get_all_preferences

def run_evaluation():
    print("🧪 MILESTONE 4: MEMORY & LEARNING EVALUATION")
    print("=" * 60)
    
    # Setup: Ensure fresh DB for test
    conn = sqlite3.connect("agent_memory.sqlite")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS user_preferences")
    cursor.execute("DROP TABLE IF EXISTS learning_history")
    conn.commit()
    conn.close()
    
    init_memory()
    
    # Configure graph with checkpointer
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)
    
    # We now compile the app explicitly for the evaluation script
    # to include the checkpointer (since we removed it from the main graph file for Studio compatibility)
    app = builder.compile(
        checkpointer=memory,
        interrupt_before=["human_decision"]
    )
    
    config = {"configurable": {"thread_id": "eval_m4_001"}}
    
    # --------------------------------------------------
    # TEST CASE 1: First interaction (Unknown preference)
    # --------------------------------------------------
    email_text = "Subject: Meeting\n\nHi agent, please email Bob about the project."
    inputs = {
        "sender": "Boss <boss@company.com>",
        "subject": "Task",
        "body": "Email Bob about the project.",
        "user_preferences": {} # Start empty in state
    }
    
    print("\n1️⃣  RUNNING TEST 1: 'Email Bob' (Expect generic draft)")
    print("-" * 60)
    
    # Run until interrupt
    try:
        app.invoke(inputs, config=config)
    except Exception:
        pass # Expected interrupt
        
    state_1 = app.get_state(config)
    draft_1 = state_1.values.get("generated_body", "")
    print(f"🤖 Agent Draft 1:\n{draft_1}")
    
    # --------------------------------------------------
    # SIMULATE HUMAN EDIT (Teaching "Robert")
    # --------------------------------------------------
    print("\n✍️  Simulating Human Edit: 'Bob' -> 'Robert'")
    
    # Create the corrected version
    corrected_body = draft_1.replace("Bob", "Robert")
    if corrected_body == draft_1:
        # Fallback if agent didn't use the name Bob
        corrected_body = "Hi Robert,\n\n" + draft_1
        
    print(f"📝 Corrected Draft:\n{corrected_body}")
    
    # Update state to simulate the edit
    app.update_state(
        config,
        {"generated_body": corrected_body, "human_decision": "approve"},
        as_node="hitl_checkpoint" # Update state at the checkpoint so 'human_decision' actually runs next
    )
    
    # Resume execution (this triggers human_decision_node -> learning)
    print("▶️  Resuming to trigger learning...")
    result = app.invoke(None, config=config)
    
    # --------------------------------------------------
    # CHECK MEMORY
    # --------------------------------------------------
    print("\n🧠 Checking Memory...")
    prefs = get_all_preferences()
    print(f"   Current Preferences: {prefs}")
    
    # --------------------------------------------------
    # TEST CASE 2: Second interaction (Should use 'Robert')
    # --------------------------------------------------
    print("\n2️⃣  RUNNING TEST 2: 'Email Bob again' (Expect 'Robert')")
    print("-" * 60)
    
    config_2 = {"configurable": {"thread_id": "eval_m4_002"}}
    inputs_2 = {
         "sender": "Boss <boss@company.com>",
        "subject": "Task 2",
        "body": "Please send another email to Bob.",
    }
    
    try:
        app.invoke(inputs_2, config=config_2)
    except Exception:
        pass
        
    state_2 = app.get_state(config_2)
    draft_2 = state_2.values.get("generated_body", "")
    
    print(f"🤖 Agent Draft 2:\n{draft_2}")
    
    # --------------------------------------------------
    # VERDICT
    # --------------------------------------------------
    if "Robert" in draft_2:
        print("\n✅ SUCCESS: Agent learned to use 'Robert'!")
    else:
        print("\n❌ FAILURE: Agent did not use 'Robert'.")

    # --------------------------------------------------
    # TEST CASE 3: Learning a Sign-off Preference
    # --------------------------------------------------
    print("\n⏳ Rate Limit Pause: Sleeping for 30s...")
    time.sleep(30)
    print("\n3️⃣  RUNNING TEST 3: Learning 'Cheers' (Expect generic sign-off)")
    print("-" * 60)
    
    config_3 = {"configurable": {"thread_id": "eval_m4_003"}}
    inputs_3 = {
         "sender": "Colleague <dave@work.com>",
        "subject": "Lunch?",
        "body": "I need a response regarding the lunch schedule. Can you confirm if 12 PM works?",
    }
    
    try:
        app.invoke(inputs_3, config=config_3)
    except Exception:
        pass
        
    state_3 = app.get_state(config_3)
    draft_3 = state_3.values.get("generated_body", "")
    print(f"🤖 Agent Draft 3:\n{draft_3}")
    
    print("\n✍️  Simulating Human Edit: 'Best regards' -> 'Cheers'")
    corrected_body_3 = draft_3.replace("Best regards", "Cheers")
    if "Cheers" not in corrected_body_3:
         corrected_body_3 += "\nCheers,"

    print(f"📝 Corrected Draft:\n{corrected_body_3}")
    
    app.update_state(
        config_3,
        {"generated_body": corrected_body_3, "human_decision": "approve"},
        as_node="hitl_checkpoint"
    )
    
    print("▶️  Resuming to trigger learning...")
    app.invoke(None, config=config_3)
    
    # --------------------------------------------------
    # TEST CASE 4: Verify Sign-off
    # --------------------------------------------------
    print("\n4️⃣  RUNNING TEST 4: 'Email Dave again' (Expect 'Cheers')")
    print("-" * 60)
    
    config_4 = {"configurable": {"thread_id": "eval_m4_004"}}
    inputs_4 = {
         "sender": "Colleague <dave@work.com>",
        "subject": "Coffee?",
        "body": "Coffee later?",
    }
    
    try:
        app.invoke(inputs_4, config=config_4)
    except Exception:
        pass
        
    state_4 = app.get_state(config_4)
    draft_4 = state_4.values.get("generated_body", "")
    print(f"🤖 Agent Draft 4:\n{draft_4}")
    
    if "Cheers" in draft_4:
        print("\n✅ SUCCESS: Agent learned to use 'Cheers'!")
    else:
        print("\n❌ FAILURE: Agent did not use 'Cheers'.")

if __name__ == "__main__":
    run_evaluation()
