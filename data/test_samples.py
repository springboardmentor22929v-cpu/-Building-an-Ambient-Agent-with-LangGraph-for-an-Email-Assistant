# data/test_samples.py

dataset = [
    # --- CATEGORY 1: RESPOND (Needs a reply) ---
    """
    - [From: Vamshi <vamshi@techstartup.com>] Subject: Project Deadline? | Body: Hi, 
    I need to know if the frontend deployment is ready for the demo tomorrow. 
    Please update me ASAP.
    """,
    """
    - [From: HR Dept <hr@company.com>] Subject: Interview Schedule | Body: 
    Hi, are you available for a quick sync-up on Friday at 2 PM IST to discuss 
    your internship progress? Let me know.
    """,
    """
    - [From: Client Support <urgency@clients.com>] Subject: SERVER DOWN | Body: 
    The production API is throwing 500 errors. We need someone to look at this 
    immediately.
    """,

    # --- CATEGORY 2: IGNORE (Spam / No Action) ---
    """
    - [From: Lottery Winner <noreply@megamillions.net>] Subject: CONGRATULATIONS! | Body: 
    You have been selected to win a $5,000 gift card. Click here to claim 
    your prize before it expires!
    """,
    """
    - [From: AWS Billing <billing@aws.amazon.com>] Subject: Invoice Available | Body: 
    Your invoice for January 2026 is now available. Total amount: $0.00. 
    No action is required.
    """,
    """
    - [From: LinkedIn <notifications@linkedin.com>] Subject: You appeared in 5 searches | Body: 
    See who is looking at your profile. 3 people from Infosys viewed your profile 
    this week.
    """,

    # --- CATEGORY 3: NOTIFY (Sensitive / Human Intervention) ---
    """
    - [From: Legal Team <legal@lawfirm.com>] Subject: URGENT: Copyright Notice | Body: 
    We have filed a lawsuit regarding your recent software release. 
    Please sign the attached documents immediately or face court action.
    """,
    """
    - [From: Boss <manager@gmail.com>] Subject: FIRING NOTICE | Body: 
    Please come to my office immediately. We need to discuss your termination 
    effective today.
    """
]