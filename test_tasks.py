from src.integrations.gmail_auth import authenticate_google_services
from src.tools.google_tools import initialize_tools, create_google_task

def test_tasks():
    print("🚀 Starting Google Tasks verification...")
    
    try:
        # 1. Authenticate (this will open a browser for new scopes)
        gmail, calendar, tasks = authenticate_google_services()
        
        # 2. Initialize tools
        initialize_tools(gmail, calendar, tasks)
        
        # 3. Test create_task tool
        result = create_google_task.invoke({
            "title": "Test Task from Email Assistant",
            "notes": "If searching this, the integration works!"
        })
        
        print(f"\nTool output:\n{result}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_tasks()
