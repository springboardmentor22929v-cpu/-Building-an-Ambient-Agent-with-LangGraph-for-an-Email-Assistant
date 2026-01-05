# Golden test dataset for triage evaluation
GOLDEN_TEST_SET = [
    # IGNORE cases
    {
        "subject": "Weekly Newsletter - Tech Updates",
        "sender": "newsletter@techblog.com",
        "content": "Here are this week's top tech stories...",
        "expected_triage": "ignore"
    },
    {
        "subject": "Your Amazon order has shipped",
        "sender": "auto-confirm@amazon.com",
        "content": "Your order #123456 has been shipped and will arrive...",
        "expected_triage": "ignore"
    },
    {
        "subject": "Spam: Get rich quick!",
        "sender": "noreply@spammer.com",
        "content": "Make $1000 in one day with this simple trick...",
        "expected_triage": "ignore"
    },
    
    # NOTIFY_HUMAN cases
    {
        "subject": "URGENT: Server outage affecting production",
        "sender": "alerts@company.com",
        "content": "Critical server failure detected. Immediate attention required.",
        "expected_triage": "notify_human"
    },
    {
        "subject": "Legal notice regarding contract",
        "sender": "legal@lawfirm.com",
        "content": "We need to discuss the terms of the upcoming contract...",
        "expected_triage": "notify_human"
    },
    {
        "subject": "Complaint about service quality",
        "sender": "angry.customer@email.com",
        "content": "I am extremely dissatisfied with the service I received...",
        "expected_triage": "notify_human"
    },
    
    # RESPOND cases
    {
        "subject": "Meeting request for next week",
        "sender": "colleague@company.com",
        "content": "Hi, could we schedule a meeting to discuss the project timeline?",
        "expected_triage": "respond"
    },
    {
        "subject": "Question about product pricing",
        "sender": "potential.customer@email.com",
        "content": "Hello, I'm interested in your product. Could you send me pricing information?",
        "expected_triage": "respond"
    },
    {
        "subject": "Thank you for the presentation",
        "sender": "client@company.com",
        "content": "Thank you for the great presentation yesterday. Looking forward to working together.",
        "expected_triage": "respond"
    },
    {
        "subject": "Request for project update",
        "sender": "manager@company.com",
        "content": "Hi, could you please provide an update on the current project status?",
        "expected_triage": "respond"
    },
    
    # Additional test cases
    {
        "subject": "Password reset confirmation",
        "sender": "security@service.com",
        "content": "Your password has been successfully reset. If this wasn't you...",
        "expected_triage": "ignore"
    },
    {
        "subject": "Invoice payment overdue",
        "sender": "billing@vendor.com",
        "content": "Your invoice #12345 is now 30 days overdue. Please remit payment...",
        "expected_triage": "notify_human"
    },
    {
        "subject": "Invitation to company event",
        "sender": "hr@company.com",
        "content": "You're invited to our annual company picnic next Friday...",
        "expected_triage": "respond"
    },
    {
        "subject": "System maintenance notification",
        "sender": "it@company.com",
        "content": "Scheduled maintenance will occur this weekend from 2-4 AM...",
        "expected_triage": "ignore"
    },
    {
        "subject": "Job application follow-up",
        "sender": "candidate@email.com",
        "content": "I wanted to follow up on my application submitted last week...",
        "expected_triage": "respond"
    },
    {
        "subject": "Data breach notification",
        "sender": "security@company.com",
        "content": "We have detected unauthorized access to our systems...",
        "expected_triage": "notify_human"
    },
    {
        "subject": "Conference registration confirmation",
        "sender": "events@conference.com",
        "content": "Thank you for registering for TechConf 2024...",
        "expected_triage": "ignore"
    },
    {
        "subject": "Request for recommendation letter",
        "sender": "former.colleague@email.com",
        "content": "Hi, I hope you're doing well. I was wondering if you could write...",
        "expected_triage": "respond"
    },
    {
        "subject": "Budget approval needed ASAP",
        "sender": "finance@company.com",
        "content": "The Q4 budget needs your approval by end of day...",
        "expected_triage": "notify_human"
    },
    {
        "subject": "Social media connection request",
        "sender": "linkedin@notifications.com",
        "content": "John Smith wants to connect with you on LinkedIn...",
        "expected_triage": "ignore"
    },
    {
        "subject": "Feedback on recent proposal",
        "sender": "client@bigcorp.com",
        "content": "We've reviewed your proposal and have some questions...",
        "expected_triage": "respond"
    }
]