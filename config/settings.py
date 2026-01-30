# config/settings.py
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# ==========================================
# 1. HELPER: KEY ROTATION LOGIC
# ==========================================
def get_first_available_key(prefix):
    """
    Searches for keys like GROQ_API_KEY, GROQ_API_KEY_1...
    Returns the first one that has a value.
    """
    # Check the main key first
    key = os.getenv(prefix)
    if key: return key
    
    # Check numbered backup keys (1 to 5)
    for i in range(1, 6):
        key = os.getenv(f"{prefix}_{i}")
        if key: return key
    
    return None

# ==========================================
# 2. MODEL SELECTION
# ==========================================
use_groq = os.getenv("USE_GROQ", "false").lower() == "true"
use_gemini = os.getenv("USE_GEMINI", "false").lower() == "true"

GROQ_MODEL_NAME = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Load API Keys using the Rotation Logic
GROQ_API_KEY = get_first_available_key("GROQ_API_KEY")
GOOGLE_API_KEY = get_first_available_key("GOOGLE_API_KEY")

# ==========================================
# 3. CONFIG CHECK
# ==========================================
print("\n--- CONFIGURATION CHECK ---")
if use_groq:
    if GROQ_API_KEY:
        print(f"✅ MODEL: Groq | Model: {GROQ_MODEL_NAME}")
    else:
        print("❌ ERROR: USE_GROQ is true, but no key found.")
elif use_gemini:
    if GOOGLE_API_KEY:
        print(f"✅ MODEL: Gemini | Model: {GEMINI_MODEL_NAME}")
    else:
        print("❌ ERROR: USE_GEMINI is true, but no key found.")
print("---------------------------\n")