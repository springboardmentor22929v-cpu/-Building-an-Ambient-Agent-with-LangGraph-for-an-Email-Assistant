# langsmith_setup.py

import os
from langsmith import Client
from dotenv import load_dotenv

# Load environment variables from .env automatically
load_dotenv()

# Required environment variables for LangSmith
REQUIRED_ENV_VARS = [
    "LANGCHAIN_API_KEY",       # LangSmith API key
    "LANGCHAIN_TRACING_V2",   # Enable tracing (set to "true")
    "LANGCHAIN_PROJECT",      # Project name
]

def validate_env_vars():
    """
    Validate that all required environment variables are set.
    Returns True if all exist, False otherwise.
    """
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file or environment:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return False
    return True

def setup_langsmith():
    """
    Set up LangSmith client for the project.
    Returns a LangSmith Client instance if successful, None otherwise.
    """
    if not validate_env_vars():
        return None

    try:
        client = Client()
        print("✅ LangSmith setup completed successfully!")
        print(f"Project: {os.getenv('LANGCHAIN_PROJECT')}")
        print(f"Tracing enabled: {os.getenv('LANGCHAIN_TRACING_V2')}")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize LangSmith Client: {e}")
        return None

def get_langsmith_client():
    """
    Shortcut to get a LangSmith client instance.
    Ensures environment variables are loaded and client initialized.
    """
    return setup_langsmith()

if __name__ == "__main__":
    setup_langsmith()
