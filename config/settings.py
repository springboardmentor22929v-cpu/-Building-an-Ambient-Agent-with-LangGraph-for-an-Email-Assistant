import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# ==========================================
# 1. HELPER: KEY ROTATION LOGIC
# ==========================================
def get_first_available_key(prefix):
    """
    Searches for keys like GROQ_API_KEY, GROQ_API_KEY_1, GROQ_API_KEY_2...
    Returns the first one that has a value.
    """
    # Check the main key first (e.g., "GROQ_API_KEY")
    key = os.getenv(prefix)
    if key: return key
    
    # Check numbered backup keys (e.g., "GROQ_API_KEY_1" to "GROQ_API_KEY_5")
    for i in range(1, 6):
        key = os.getenv(f"{prefix}_{i}")
        if key: return key
    
    return None

# ==========================================
# 2. MODEL SELECTION
# ==========================================
# Read boolean flags (Default to false to avoid accidents)
use_groq = os.getenv("USE_GROQ", "false").lower() == "true"
use_gemini = os.getenv("USE_GEMINI", "false").lower() == "true"

# Load Model Names
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Load API Keys using the Rotation Logic
GROQ_API_KEY = get_first_available_key("GROQ_API_KEY")
GOOGLE_API_KEY = get_first_available_key("GOOGLE_API_KEY")

# ==========================================
# 3. TOOL SELECTION (Real vs Mock)
# ==========================================
use_real_tools = os.getenv("USE_REAL_TOOLS", "false").lower() == "true"

# ==========================================
# 4. CONFIGURATION CHECK (Print status)
# ==========================================
print("\n--- CONFIGURATION CHECK ---")

# Check Model Status
if use_groq:
    if GROQ_API_KEY:
        print(f"✅ MODEL: Groq (Llama 3) | Model: {GROQ_MODEL_NAME}")
        print("   -> API Key Found.")
    else:
        print("❌ ERROR: USE_GROQ is true, but no GROQ_API_KEY found.")

elif use_gemini:
    if GOOGLE_API_KEY:
        print(f"✅ MODEL: Gemini (Google) | Model: {GEMINI_MODEL_NAME}")
        print("   -> API Key Found.")
    else:
        print("❌ ERROR: USE_GEMINI is true, but no GOOGLE_API_KEY found.")
else:
    print("⚠️  WARNING: No Model Selected (Both USE_GROQ and USE_GEMINI are false)")

# Check Tool Status
if use_real_tools:
    print("✅ MODE: REAL TOOLS (Using Gmail API)")
    if not os.path.exists("credentials.json"):
        print("   ⚠️  WARNING: 'credentials.json' missing! Real Gmail will fail.")
else:
    print("✅ MODE: MOCK TOOLS (Safe for testing)")

print("---------------------------\n")