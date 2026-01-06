import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

def test_gemini_connection():
    """Test basic connection to Google Gemini API."""
    
    try:
        # Try different model names
        models_to_try = [
            "gemini-1.5-pro",
            "gemini-pro",
            "gemini-1.0-pro"
        ]
        
        for model_name in models_to_try:
            print(f"Testing model: {model_name}")
            try:
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    temperature=0.1
                )
                
                response = llm.invoke([HumanMessage(content="Hello, can you respond with 'API working'?")])
                print(f"SUCCESS: {model_name} works! Response: {response.content}")
                return model_name
                
            except Exception as e:
                print(f"FAILED: {model_name} - {str(e)[:100]}...")
                continue
        
        print("ERROR: No working models found")
        return None
        
    except Exception as e:
        print(f"ERROR: Connection failed - {e}")
        return None

if __name__ == "__main__":
    working_model = test_gemini_connection()
    if working_model:
        print(f"\nSUCCESS: Use model: {working_model}")
    else:
        print("\nERROR: Check your API key and try again")