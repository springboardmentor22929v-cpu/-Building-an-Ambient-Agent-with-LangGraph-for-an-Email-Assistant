from dotenv import load_dotenv
import os

load_dotenv()

# Test 1: Environment variables
print("✓ GOOGLE_API_KEY:", "✓" if os.getenv("GOOGLE_API_KEY") else "✗")
print("✓ LANGCHAIN_API_KEY:", "✓" if os.getenv("LANGCHAIN_API_KEY") else "✗")

# Test 2: LangChain imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.graph import StateGraph
    print("✓ LangChain imports successful")
except ImportError as e:
    print("✗ Import error:", e)

# Test 3: Gemini API
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    response = llm.invoke("Say 'Setup complete!'")
    print("✓ Gemini API:", response.content)
except Exception as e:
    print("✗ Gemini error:", e)

print("\n🎉 Setup complete! Ready to build.")
