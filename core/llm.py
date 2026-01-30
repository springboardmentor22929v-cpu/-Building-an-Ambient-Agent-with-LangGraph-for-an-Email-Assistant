# core/llm.py
from config.settings import (
    use_groq, 
    use_gemini, 
    GROQ_API_KEY, 
    GOOGLE_API_KEY,
    GROQ_MODEL_NAME,
    GEMINI_MODEL_NAME
)
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(temperature=0):
    """
    Returns the configured LLM based on settings.py logic.
    """
    if use_groq:
        if not GROQ_API_KEY:
            raise ValueError("❌ Groq selected but NO API KEY found.")
        return ChatGroq(
            model=GROQ_MODEL_NAME,
            api_key=GROQ_API_KEY,
            temperature=temperature
        )
    
    elif use_gemini:
        if not GOOGLE_API_KEY:
            raise ValueError("❌ Gemini selected but NO API KEY found.")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL_NAME,
            api_key=GOOGLE_API_KEY,
            temperature=temperature
        )
    
    else:
        raise ValueError("❌ No Model Selected in .env (Check USE_GROQ/USE_GEMINI)")