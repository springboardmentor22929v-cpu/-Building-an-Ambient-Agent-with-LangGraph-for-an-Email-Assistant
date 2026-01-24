# tools/mock_tools.py

# Import the @tool decorator from LangChain.
# This tells the AI: "This function is a tool you can use."
from langchain_core.tools import tool

@tool
def write_email(to: str, subject: str, content: str) -> str:
    """
    Simulates sending an email.
    It does NOT send anything. It just prints the details to the screen.
    """
    
    # Print a visual border to make it look nice in the terminal.
    print(f"\n📨 [MOCK EMAIL SENT] -----------------------------")
    
    # Print who the email is for.
    print(f"   To:      {to}")
    
    # Print the subject line.
    print(f"   Subject: {subject}")
    
    # Print the actual body of the email.
    print(f"   Content: {content}")
    
    # Print the closing border.
    print(f"---------------------------------------------------\n")
    
    # Return a success message to the AI.
    # The AI reads this string to know that the tool worked correctly.
    return "✅ Mock email sent successfully."

@tool
def check_calendar(date: str) -> str:
    """
    Simulates checking a calendar.
    It returns fake data so we can test if the AI understands dates.
    """
    
    # We return a specific string pretending to be a calendar event.
    # The AI will read this and think: "Oh, the user is busy at 10 AM."
    return f"📅 [MOCK CALENDAR] On {date}, you have a meeting at 10:00 AM. The rest of the day is free."