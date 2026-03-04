triage_system_prompt = """You are an expert email triage assistant. 
Classify the email into: 'ignore', 'notify_human', or 'respond'."""

triage_user_prompt = "Please classify this email: {email_thread}"

default_triage_instructions = "Focus on identifying if the email is spam (ignore), informational (notify), or a request (respond)."

default_background = "You are assisting a busy professional manage their inbox."


# prompts.py

# The core system prompt for your agent node
agent_system_prompt = """
You are a helpful AI assistant. 
{background}

{tools_prompt}

Your preferences for responding are:
{response_preferences}

Your calendar preferences are:
{cal_preferences}
"""

default_background = "You are helping a busy professional triage and respond to their inbox."
default_response_preferences = "Keep responses professional, concise, and helpful."
default_cal_preferences = "Always check for conflicts before suggesting a time."

# (Include your triage prompts from the previous step here too)
triage_system_prompt = "You are an email triage assistant..."