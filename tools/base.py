# tools/base.py

# Import the 'use_real_tools' variable from our settings file.
# This variable is True if you set USE_REAL_TOOLS=true in .env, otherwise False.
from config.settings import use_real_tools

# Import the module containing the REAL Gmail functions.
# We rename it to 'real' so it's easier to type later.
import tools.real_tools as real

# Import the module containing the FAKE (Mock) functions.
# We rename it to 'mock' so it's easier to type later.
import tools.mock_tools as mock

def get_tools():
    """
    This function acts as a switch.
    It checks your .env settings and returns the correct list of tools.
    """
    
    # Check if the user wants to use Real Tools (True)
    if use_real_tools:
        # Print a message to the console so the user knows what is happening.
        print("🔧 [SYSTEM] Loading REAL Gmail Tools...")
        
        # Return the list of real functions.
        # These functions will actually connect to Google.
        return [real.write_email, real.check_calendar]
        
    else:
        # If use_real_tools is False, we use the Mock tools.
        # Print a message to confirm we are in Safe Mode.
        print("🔧 [SYSTEM] Loading MOCK Tools (Safe Mode)...")
        
        # Return the list of fake functions.
        # These functions just print text and won't send anything.
        return [mock.write_email, mock.check_calendar]