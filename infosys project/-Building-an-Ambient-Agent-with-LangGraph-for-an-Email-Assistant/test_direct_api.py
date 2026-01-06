import os
from dotenv import load_dotenv

load_dotenv()

def test_direct_api():
    """Test direct Google Generative AI API."""
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("ERROR: No API key found in .env file")
            return False
            
        print(f"API Key found: {api_key[:10]}...")
        
        genai.configure(api_key=api_key)
        
        # List available models
        print("\\nAvailable models:")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"- {model.name}")
        
        # Try to use a model
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello, respond with 'API working'")
        print(f"\\nSUCCESS: {response.text}")
        return True
        
    except ImportError:
        print("Installing google-generativeai...")
        os.system("pip install google-generativeai")
        return test_direct_api()
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_direct_api()