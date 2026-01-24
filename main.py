# main.py

# ==========================================
# 1. IMPORTS
# ==========================================
# Import the HumanMessage class. This is used to wrap the email text
# so the AI understands it comes from a "Human" user.
from langchain_core.messages import HumanMessage

# Import the 'app' variable from our agent file.
# This 'app' is the compiled Graph (the entire brain of the bot).
from core.agent import app

# Import the 'use_real_tools' setting.
# We use this just to print a confirmation message at the start.
from config.settings import use_real_tools

# ==========================================
# 2. HELPER FUNCTION: RUN A SINGLE TEST
# ==========================================
def run_test_email(email_text):
    """
    This function takes a raw string of email text, sends it to the AI,
    and prints the result. It handles the entire process for one email.
    """
    
    # Print a visual separator line to make the output easy to read.
    print(f"\n{'='*60}")
    
    # Print the input email so we can see what we are testing.
    print(f"📩 INPUT EMAIL:\n{email_text}")
    print(f"{'='*60}")

    # ----------------------------------
    # STEP 1: PREPARE THE INPUT
    # ----------------------------------
    # The agent expects a state dictionary with a key "messages".
    # We wrap our email text in a HumanMessage object.
    initial_state = {"messages": [HumanMessage(content=email_text)]}

    # ----------------------------------
    # STEP 2: RUN THE AGENT (THE BRAIN)
    # ----------------------------------
    # We use a try-except block to catch any errors that might crash the program.
    try:
        # app.invoke(initial_state) starts the graph workflow.
        # It goes Triage -> (Maybe Action) -> End.
        # 'final_state' holds the memory of the agent after it finishes.
        final_state = app.invoke(initial_state)
        
        # ----------------------------------
        # STEP 3: CHECK THE RESULT
        # ----------------------------------
        # Extract the decision category ('ignore', 'respond', or 'notify')
        # that the Triage Node decided on.
        category = final_state["email_category"]
        
        # LOGIC: Did the agent decide to write a reply?
        if category == "respond":
            # If yes, the Action Node ran.
            # The drafted email will be the LAST message in the 'messages' list.
            last_message = final_state['messages'][-1].content
            
            # Print the drafted email response.
            print(f"\n📬 FINAL OUTPUT (Drafted Reply):\n{last_message}")
        else:
            # If no, the agent skipped the Action Node.
            # We just print what category it filed the email under.
            print(f"\n🛑 FINAL OUTPUT: [Filed as {category.upper()}] - No reply needed.")
            
    except Exception as e:
        # If anything crashed (like an API error), print the error message here.
        print(f"❌ ERROR: {e}")

# ==========================================
# 3. MAIN EXECUTION BLOCK
# ==========================================
# This block runs only if you execute 'python main.py' directly.
if __name__ == "__main__":
    
    # Print a welcome message to confirm the script is starting.
    print("🚀 STARTING AMBIENT AGENT...")
    
    # Check our settings one last time to tell the user what mode we are in.
    if use_real_tools:
        print("   (Mode: REAL - Connecting to Gmail...)")
    else:
        print("   (Mode: MOCK - Using simulation tools)")
    
    # ==========================================
    # TEST CASE 1: A Work Request
    # ==========================================
    # This email asks for a meeting. The agent SHOULD:
    # 1. Triage it as 'RESPOND'.
    # 2. Use the Calendar Tool (Mock or Real) to check availability.
    # 3. Draft a reply proposing a time.
    email_1 = """
    From: vuthuluriamar@gmail.com
    To: amarvinesh5264@gmail.com
    Subject: Meeting Request
    
    Hi,
    Can we schedule a meeting for Thursday at 2 PM?
    """
    # Run the helper function with this email.
    run_test_email(email_1)

    # ==========================================
    # TEST CASE 2: Spam
    # ==========================================
    # This is obvious spam. The agent SHOULD:
    # 1. Triage it as 'IGNORE'.
    # 2. Stop immediately (No Action Node).
    # email_2 = """
    # Subject: YOU WON A LOTTERY!
    # Click here to claim your $1,000,000 prize now!
    # """
    # # Run the helper function with this email.
    # run_test_email(email_2)