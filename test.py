print("Checking imports...")

try:
    from langchain_core.pydantic_v1 import SecretStr
    print("✓ langchain-core installed correctly")
except ImportError as e:
    print(f"✗ langchain-core issue: {e}")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("✓ langchain-google-genai installed correctly")
except ImportError as e:
    print(f"✗ langchain-google-genai issue: {e}")

try:
    from langgraph.graph import StateGraph
    print("✓ langgraph installed correctly")
except ImportError as e:
    print(f"✗ langgraph issue: {e}")

try:
    from dotenv import load_dotenv
    print("✓ python-dotenv installed correctly")
except ImportError as e:
    print(f"✗ python-dotenv issue: {e}")

print("\n✅ All imports successful!")