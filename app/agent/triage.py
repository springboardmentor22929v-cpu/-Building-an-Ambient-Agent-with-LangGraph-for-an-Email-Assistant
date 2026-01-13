from app.llm.gemini import llm


def triage_email(state):
    email = state["email"]

    prompt = f"""
You are an email triage assistant helping ONE specific user manage their inbox.

The goal is to reduce noise and show only what truly matters.

==================================================
USER CONTEXT
==================================================
- The user is a student / intern.
- The user receives many promotional, platform, and congratulatory emails.
- The user does NOT want to be notified for such emails.

==================================================
TRIAGE CATEGORIES
==================================================

1) ignore
Use this when the email is:
- Promotional or marketing
- Internship / job platform emails (Internshala, Unstop, LinkedIn, etc.)
- Congratulatory or onboarding emails
- Partnership emails
- Surveys, newsletters, advertisements
- Anything that does NOT require action or attention

Examples:
- Subject: "Congrats on taking the first step"
- Subject: "Hiring now: opportunities on Internshala"
- Subject: "Unstop partnership email"
- Subject: "Invitation to participate in a survey"

→ Decision: ignore

--------------------------------------------------

2) notify_human
Use this when the email is important but does NOT require a reply:
- Security alerts
- Account access warnings
- Policy or terms updates
- System notifications

Examples:
- Subject: "Security alert"
- Subject: "Your Google account access was updated"
- Subject: "Changes to Terms of Service"

→ Decision: notify_human

--------------------------------------------------

3) respond_or_act
Use this when the email requires a reply or action:
- Mentor or manager emails
- Meeting requests
- Approval or confirmation requests
- Direct questions

Examples:
- Subject: "Please confirm your availability"
- Subject: "Action required: approve budget"
- Subject: "Kick-off meeting schedule"

→ Decision: respond_or_act

==================================================
INSTRUCTIONS
==================================================
- Decide strictly based on the rules and examples above.
- Do NOT treat congratulatory or platform emails as important.
- Output ONLY one of the following labels:
  ignore OR notify_human OR respond_or_act

==================================================
EMAIL TO CLASSIFY
==================================================
{email}
"""

    decision = llm.invoke(prompt).content.strip().lower()

    return {
        "email": email,
        "decision": decision
    }
