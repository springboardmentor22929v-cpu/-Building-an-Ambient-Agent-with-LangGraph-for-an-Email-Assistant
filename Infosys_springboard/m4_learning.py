from google import genai
import os
from dotenv import load_dotenv
from m4_memory import store_preference, log_learning_event

load_dotenv()

# Configure Gemini (New SDK)
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def learn_from_correction(original_draft: str, final_draft: str):
    """
    Analyze the difference between the original draft and the final draft.
    Extract the underlying preference or rule and update memory.
    """
    print("🧠 LEARNING: Analyzing human correction...")
    
    prompt = f"""
    You are an AI learning from human feedback.
    
    ORIGINAL DRAFT (by Agent):
    {original_draft}
    
    FINAL DRAFT (Corrected by Human):
    {final_draft}
    
    Task:
    1. Identify what changed (tone, specific words, formatting, facts).
    2. Extract a generalizable rule or preference from this change.
    3. Return ONLY the rule as a concise key-value pair in format: KEY: VALUE
    
    Examples:
    - Change: "Hi Bob" -> "Dear Mr. Smith"
      Output: greeting_style: Formal (Dear Mr. X)
      
    - Change: "Email Bob" -> "Email Robert"
      Output: preferred_name_bob: Robert

    - Change: "I can meet at 2" -> "I can meet at 2 PM EST"
      Output: time_format: Always specify timezone
      
    - Change: "Best," -> "Cheers,"
      Output: sign_off: Cheers
      
    If the change is trivial (typo) or specific to this one email (just a date change), return "None".
    """
    
    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )
        result = response.text.strip()
        
        if "None" in result or ":" not in result:
            print("🧠 Learning skipped (no generalizable preference found).")
            return

        # Parse "Key: Value"
        try:
            key, value = result.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            
            print(f"💡 LEARNED NEW PREFERENCE: {key} = {value}")
            
            # 1. Update Memory
            store_preference(key, value)
            
            # 2. Log for evaluation
            log_learning_event(original_draft, final_draft, f"{key}: {value}")
            
            return f"{key}: {value}"
        except ValueError:
             print(f"⚠️ Could not parse result: {result}")
        
    except Exception as e:
        print(f"❌ Error in learning loop: {e}")
