import json
from typing import List, Dict, Literal

# Golden dataset for triage evaluation
GOLDEN_EMAILS = [
    # IGNORE category (spam, newsletters, irrelevant)
    {
        "id": 1,
        "sender": "noreply@newsletter.com",
        "subject": "Weekly Newsletter - Tech Updates",
        "content": "Here are this week's top tech stories...",
        "expected_triage": "ignore",
        "category": "newsletter"
    },
    {
        "id": 2,
        "sender": "promotions@store.com",
        "subject": "50% OFF Everything - Limited Time!",
        "content": "Don't miss out on our biggest sale of the year!",
        "expected_triage": "ignore",
        "category": "promotional"
    },
    {
        "id": 3,
        "sender": "spam@random.com",
        "subject": "You've won $1,000,000!",
        "content": "Congratulations! Click here to claim your prize...",
        "expected_triage": "ignore",
        "category": "spam"
    },
    {
        "id": 4,
        "sender": "updates@social.com",
        "subject": "You have 5 new notifications",
        "content": "Check out what's happening in your network...",
        "expected_triage": "ignore",
        "category": "social_media"
    },
    {
        "id": 5,
        "sender": "noreply@bank.com",
        "subject": "Your monthly statement is ready",
        "content": "Your account statement for this month is now available...",
        "expected_triage": "ignore",
        "category": "automated"
    },
    
    # NOTIFY_HUMAN category (urgent, sensitive, complex)
    {
        "id": 6,
        "sender": "ceo@company.com",
        "subject": "URGENT: Board Meeting Tomorrow",
        "content": "We need to discuss the quarterly results immediately. Please prepare the financial reports.",
        "expected_triage": "notify_human",
        "category": "urgent_executive"
    },
    {
        "id": 7,
        "sender": "hr@company.com",
        "subject": "Confidential: Performance Review Discussion",
        "content": "We need to schedule a private meeting to discuss your team member's performance issues.",
        "expected_triage": "notify_human",
        "category": "sensitive_hr"
    },
    {
        "id": 8,
        "sender": "legal@company.com",
        "subject": "Contract Dispute - Immediate Action Required",
        "content": "Our client is threatening legal action. We need to review the contract terms urgently.",
        "expected_triage": "notify_human",
        "category": "legal_urgent"
    },
    {
        "id": 9,
        "sender": "client@bigcorp.com",
        "subject": "Project Cancellation Notice",
        "content": "Due to budget constraints, we need to cancel the project effective immediately.",
        "expected_triage": "notify_human",
        "category": "business_critical"
    },
    {
        "id": 10,
        "sender": "security@company.com",
        "subject": "Security Breach Alert",
        "content": "We've detected unusual activity on your account. Please change your password immediately.",
        "expected_triage": "notify_human",
        "category": "security_alert"
    },
    
    # RESPOND category (can be handled automatically)
    {
        "id": 11,
        "sender": "colleague@company.com",
        "subject": "Meeting Request - Next Week",
        "content": "Hi, can we schedule a meeting next week to discuss the project timeline?",
        "expected_triage": "respond",
        "category": "meeting_request"
    },
    {
        "id": 12,
        "sender": "team@company.com",
        "subject": "Status Update Request",
        "content": "Could you please provide a status update on the current project?",
        "expected_triage": "respond",
        "category": "status_request"
    },
    {
        "id": 13,
        "sender": "support@vendor.com",
        "subject": "Re: Technical Question",
        "content": "Thank you for your inquiry. Here's the information you requested about our API...",
        "expected_triage": "respond",
        "category": "informational"
    },
    {
        "id": 14,
        "sender": "assistant@company.com",
        "subject": "Calendar Confirmation",
        "content": "Your meeting with the client has been scheduled for Friday at 2 PM. Please confirm.",
        "expected_triage": "respond",
        "category": "confirmation"
    },
    {
        "id": 15,
        "sender": "partner@company.com",
        "subject": "Quick Question About Documentation",
        "content": "Hi, I'm looking for the latest API documentation. Could you point me in the right direction?",
        "expected_triage": "respond",
        "category": "simple_question"
    },
    
    # Additional test cases for edge cases
    {
        "id": 16,
        "sender": "intern@company.com",
        "subject": "Help with Project Setup",
        "content": "I'm new to the team and need help setting up my development environment.",
        "expected_triage": "respond",
        "category": "help_request"
    },
    {
        "id": 17,
        "sender": "manager@company.com",
        "subject": "Budget Approval Needed",
        "content": "The team needs approval for additional software licenses. Total cost: $500.",
        "expected_triage": "notify_human",
        "category": "approval_required"
    },
    {
        "id": 18,
        "sender": "customer@client.com",
        "subject": "Thank you for the demo",
        "content": "The product demo was great! We're interested in moving forward with a pilot program.",
        "expected_triage": "notify_human",
        "category": "sales_opportunity"
    },
    {
        "id": 19,
        "sender": "developer@company.com",
        "subject": "Code Review Request",
        "content": "I've submitted a pull request for the new feature. Could you review it when you have time?",
        "expected_triage": "respond",
        "category": "code_review"
    },
    {
        "id": 20,
        "sender": "noreply@github.com",
        "subject": "Pull Request Merged",
        "content": "Your pull request #123 has been merged into the main branch.",
        "expected_triage": "ignore",
        "category": "automated_notification"
    },
    {
        "id": 21,
        "sender": "recruiter@company.com",
        "subject": "Interview Feedback Required",
        "content": "Please provide feedback on the candidate we interviewed yesterday.",
        "expected_triage": "notify_human",
        "category": "hiring_decision"
    },
    {
        "id": 22,
        "sender": "vendor@supplier.com",
        "subject": "Invoice #12345",
        "content": "Please find attached invoice #12345 for services rendered last month.",
        "expected_triage": "respond",
        "category": "invoice"
    },
    {
        "id": 23,
        "sender": "emergency@company.com",
        "subject": "Server Outage - All Hands",
        "content": "Production servers are down. All engineering team members please join the war room.",
        "expected_triage": "notify_human",
        "category": "emergency"
    },
    {
        "id": 24,
        "sender": "colleague@company.com",
        "subject": "Lunch Plans?",
        "content": "Want to grab lunch today? I'm free around 12:30.",
        "expected_triage": "respond",
        "category": "casual"
    },
    {
        "id": 25,
        "sender": "training@company.com",
        "subject": "Mandatory Security Training Reminder",
        "content": "This is a reminder that you need to complete your annual security training by Friday.",
        "expected_triage": "respond",
        "category": "training_reminder"
    },
    # Additional emails for expanded dataset (10 more to reach 35 total)
    {
        "id": 26,
        "sender": "noreply@linkedin.com",
        "subject": "You have 3 new connection requests",
        "content": "Check out who wants to connect with you on LinkedIn...",
        "expected_triage": "ignore",
        "category": "social_networking"
    },
    {
        "id": 27,
        "sender": "discounts@retail.com",
        "subject": "Flash Sale: 70% OFF All Items!",
        "content": "Limited time offer! Shop now before it's too late.",
        "expected_triage": "ignore",
        "category": "promotional_sale"
    },
    {
        "id": 28,
        "sender": "board@company.com",
        "subject": "Board Meeting Agenda - Executive Decision Required",
        "content": "We need to make critical decisions about the company's strategic direction.",
        "expected_triage": "notify_human",
        "category": "executive_decision"
    },
    {
        "id": 29,
        "sender": "compliance@company.com",
        "subject": "URGENT: GDPR Compliance Violation",
        "content": "We've received a complaint about data handling practices. Immediate investigation required.",
        "expected_triage": "notify_human",
        "category": "compliance_issue"
    },
    {
        "id": 30,
        "sender": "prospect@potentialclient.com",
        "subject": "Interest in Your Services",
        "content": "We saw your website and are interested in discussing a potential partnership.",
        "expected_triage": "notify_human",
        "category": "business_opportunity"
    },
    {
        "id": 31,
        "sender": "colleague@company.com",
        "subject": "Can we reschedule our 1:1?",
        "content": "Something came up. Can we move our meeting to next Tuesday instead?",
        "expected_triage": "respond",
        "category": "meeting_reschedule"
    },
    {
        "id": 32,
        "sender": "teamlead@company.com",
        "subject": "Project Deadline Extension Request",
        "content": "Due to unforeseen circumstances, we need a 2-week extension on the project deadline.",
        "expected_triage": "respond",
        "category": "deadline_request"
    },
    {
        "id": 33,
        "sender": "it@company.com",
        "subject": "Password Reset Instructions",
        "content": "Follow these steps to reset your account password securely.",
        "expected_triage": "respond",
        "category": "it_support"
    },
    {
        "id": 34,
        "sender": "noreply@slack.com",
        "subject": "New message in #general",
        "content": "You have unread messages in your Slack workspace.",
        "expected_triage": "ignore",
        "category": "slack_notification"
    },
    {
        "id": 35,
        "sender": "finance@company.com",
        "subject": "Expense Report Approval",
        "content": "Your expense report for last month is ready for approval. Total: $1,250.",
        "expected_triage": "notify_human",
        "category": "expense_approval",
        "expected_response": ""
    },
    # Additional emails for expanded dataset (65 more to reach 100 total)
    {
        "id": 36,
        "sender": "colleague@company.com",
        "subject": "Quick Question About the Report",
        "content": "Hi, I was wondering if you could clarify the numbers in section 3 of the quarterly report. The variance seems off.",
        "expected_triage": "respond",
        "category": "clarification_request",
        "expected_response": "Hi [Colleague], The variance in section 3 is due to the one-time adjustment we made for the equipment upgrade costs. I've attached a breakdown for clarity. Let me know if you need any additional details."
    },
    {
        "id": 37,
        "sender": "vendor@software.com",
        "subject": "License Renewal Reminder",
        "content": "Your software license expires in 30 days. Please renew to avoid service interruption.",
        "expected_triage": "respond",
        "category": "renewal_reminder",
        "expected_response": "Thank you for the reminder. I've initiated the renewal process for our software license. The payment will be processed within the next billing cycle."
    },
    {
        "id": 38,
        "sender": "recruiter@agency.com",
        "subject": "Candidate Interview Availability",
        "content": "The candidate for the senior developer position is available for interviews next week. Please let me know your availability.",
        "expected_triage": "notify_human",
        "category": "recruiting_interview",
        "expected_response": ""
    },
    {
        "id": 39,
        "sender": "customer@client.com",
        "subject": "Feature Request: API Integration",
        "content": "We're interested in integrating your API with our platform. Could you provide documentation and pricing?",
        "expected_triage": "respond",
        "category": "feature_request",
        "expected_response": "Thank you for your interest in our API integration. I've attached the complete API documentation and pricing information. Our integration specialist will follow up within 24 hours to discuss your specific requirements."
    },
    {
        "id": 40,
        "sender": "noreply@eventbrite.com",
        "subject": "Your Event Registration Confirmation",
        "content": "Thank you for registering for the Tech Conference 2024. Your ticket is attached.",
        "expected_triage": "ignore",
        "category": "event_confirmation",
        "expected_response": ""
    },
    {
        "id": 41,
        "sender": "manager@company.com",
        "subject": "Performance Review Meeting",
        "content": "Let's schedule your quarterly performance review. I'm available next Tuesday or Wednesday afternoon.",
        "expected_triage": "respond",
        "category": "performance_review",
        "expected_response": "Thank you for scheduling the performance review. Tuesday afternoon works best for me. I've added it to my calendar for 2 PM."
    },
    {
        "id": 42,
        "sender": "security@company.com",
        "subject": "Password Policy Update",
        "content": "Effective next month, all passwords must be at least 12 characters and include special characters.",
        "expected_triage": "respond",
        "category": "policy_update",
        "expected_response": "Understood. I'll update my password to meet the new requirements before the deadline. Thank you for the advance notice."
    },
    {
        "id": 43,
        "sender": "partner@alliance.com",
        "subject": "Joint Marketing Campaign Proposal",
        "content": "We're proposing a co-branded marketing campaign for Q1. Please review the attached proposal.",
        "expected_triage": "notify_human",
        "category": "partnership_proposal",
        "expected_response": ""
    },
    {
        "id": 44,
        "sender": "it@company.com",
        "subject": "System Maintenance Notice",
        "content": "Scheduled maintenance will occur this Saturday from 2-4 AM. Services will be unavailable during this time.",
        "expected_triage": "respond",
        "category": "maintenance_notice",
        "expected_response": "Thank you for the maintenance notice. I've noted the downtime and will plan accordingly. Please send a reminder closer to the date."
    },
    {
        "id": 45,
        "sender": "client@enterprise.com",
        "subject": "Contract Extension Discussion",
        "content": "Our current contract expires in 60 days. We'd like to discuss extension terms and potential updates.",
        "expected_triage": "notify_human",
        "category": "contract_negotiation",
        "expected_response": ""
    },
    {
        "id": 46,
        "sender": "team@company.com",
        "subject": "Team Building Event RSVP",
        "content": "We're organizing a team building event next Friday. Please RSVP by Wednesday.",
        "expected_triage": "respond",
        "category": "event_rsvp",
        "expected_response": "I'll be attending the team building event next Friday. Looking forward to it!"
    },
    {
        "id": 47,
        "sender": "support@cloudprovider.com",
        "subject": "Service Outage Notification",
        "content": "We're experiencing a regional outage affecting some customers. Estimated resolution time is 2 hours.",
        "expected_triage": "respond",
        "category": "service_outage",
        "expected_response": "Thank you for the outage notification. I've informed the team about the potential impact. Please keep us updated on the resolution progress."
    },
    {
        "id": 48,
        "sender": "analyst@research.com",
        "subject": "Industry Report Access Request",
        "content": "I'd like to request access to your latest industry analysis report. What's the process for obtaining it?",
        "expected_triage": "respond",
        "category": "access_request",
        "expected_response": "I've submitted your access request for the industry analysis report. You should receive login credentials via email within the next business day."
    },
    {
        "id": 49,
        "sender": "noreply@surveymonkey.com",
        "subject": "Customer Satisfaction Survey",
        "content": "Please take 2 minutes to complete our customer satisfaction survey about your recent experience.",
        "expected_triage": "ignore",
        "category": "survey_request",
        "expected_response": ""
    },
    {
        "id": 50,
        "sender": "director@company.com",
        "subject": "Strategic Planning Session",
        "content": "We need to schedule an urgent strategic planning session for the upcoming product launch.",
        "expected_triage": "notify_human",
        "category": "strategic_planning",
        "expected_response": ""
    },
    {
        "id": 51,
        "sender": "freelancer@contractor.com",
        "subject": "Project Milestone Completed",
        "content": "I've completed the first milestone of the website redesign project. Please review and approve.",
        "expected_triage": "respond",
        "category": "milestone_completion",
        "expected_response": "Thank you for completing the first milestone. I've reviewed the work and it looks excellent. Payment will be processed within 24 hours."
    },
    {
        "id": 52,
        "sender": "regulatory@agency.gov",
        "subject": "Regulatory Filing Deadline",
        "content": "Reminder: Your quarterly regulatory filing is due in 7 days. Please ensure all documentation is complete.",
        "expected_triage": "notify_human",
        "category": "regulatory_deadline",
        "expected_response": ""
    },
    {
        "id": 53,
        "sender": "colleague@company.com",
        "subject": "Document Collaboration Request",
        "content": "I've shared a Google Doc with you for the presentation. Could you review and add your input by EOD?",
        "expected_triage": "respond",
        "category": "collaboration_request",
        "expected_response": "I've reviewed the Google Doc and added my comments and suggestions. Let me know if you'd like to discuss any of the points further."
    },
    {
        "id": 54,
        "sender": "marketing@company.com",
        "subject": "Content Calendar Review",
        "content": "The Q1 content calendar is ready for your review. Please provide feedback by Friday.",
        "expected_triage": "respond",
        "category": "content_review",
        "expected_response": "I've reviewed the Q1 content calendar. It looks comprehensive. I have a few suggestions for timing adjustments which I've noted in the comments."
    },
    {
        "id": 55,
        "sender": "supplier@materials.com",
        "subject": "Supply Chain Delay Notice",
        "content": "Due to weather conditions, there will be a 3-day delay in our component delivery scheduled for next week.",
        "expected_triage": "notify_human",
        "category": "supply_chain_issue",
        "expected_response": ""
    },
    {
        "id": 56,
        "sender": "student@internship.com",
        "subject": "Internship Application Follow-up",
        "content": "I applied for the summer internship position last week. Could you provide an update on my application status?",
        "expected_triage": "respond",
        "category": "application_followup",
        "expected_response": "Thank you for your patience. Your internship application is currently under review. We'll provide a final decision by the end of next week."
    },
    {
        "id": 57,
        "sender": "noreply@zoom.us",
        "subject": "Meeting Recording Available",
        "content": "The recording from today's all-hands meeting is now available. Access it using the link below.",
        "expected_triage": "ignore",
        "category": "meeting_recording",
        "expected_response": ""
    },
    {
        "id": 58,
        "sender": "auditor@accounting.com",
        "subject": "Audit Preparation Request",
        "content": "We'll be conducting the annual audit next month. Please prepare the requested financial documents.",
        "expected_triage": "notify_human",
        "category": "audit_preparation",
        "expected_response": ""
    },
    {
        "id": 59,
        "sender": "colleague@company.com",
        "subject": "Knowledge Sharing Session",
        "content": "I'm hosting a knowledge sharing session on the new testing framework next Wednesday at 3 PM. Interested?",
        "expected_triage": "respond",
        "category": "knowledge_sharing",
        "expected_response": "That sounds valuable. I'll attend the knowledge sharing session on the testing framework next Wednesday at 3 PM."
    },
    {
        "id": 60,
        "sender": "press@newsagency.com",
        "subject": "Press Release Opportunity",
        "content": "We're interested in covering your company's recent product launch. Would you be available for an interview?",
        "expected_triage": "notify_human",
        "category": "press_inquiry",
        "expected_response": ""
    },
    {
        "id": 61,
        "sender": "developer@opensource.com",
        "subject": "Open Source Contribution",
        "content": "Thank you for your recent contribution to our open source project. We'd like to discuss potential collaboration.",
        "expected_triage": "respond",
        "category": "open_source_contribution",
        "expected_response": "Thank you for the recognition. I'm interested in discussing collaboration opportunities. Please let me know your availability for a call next week."
    },
    {
        "id": 62,
        "sender": "insurance@provider.com",
        "subject": "Policy Renewal Quote",
        "content": "Your current insurance policy expires in 45 days. Here's your renewal quote with updated coverage options.",
        "expected_triage": "respond",
        "category": "insurance_renewal",
        "expected_response": "Thank you for the renewal quote. I'll review the updated coverage options and get back to you within the next few days."
    },
    {
        "id": 63,
        "sender": "mentor@company.com",
        "subject": "Mentorship Program Check-in",
        "content": "How are things going? Let's schedule our monthly mentorship check-in to discuss your progress and goals.",
        "expected_triage": "respond",
        "category": "mentorship_checkin",
        "expected_response": "Things are going well. I'm available for our monthly mentorship check-in. How about Thursday afternoon?"
    },
    {
        "id": 64,
        "sender": "conference@industry.org",
        "subject": "Speaker Proposal Submission",
        "content": "Thank you for submitting your speaker proposal for our annual conference. We'll notify you of the decision by March 1st.",
        "expected_triage": "respond",
        "category": "conference_speaker",
        "expected_response": "Thank you for the update on my speaker proposal. I look forward to hearing from you by March 1st."
    },
    {
        "id": 65,
        "sender": "data@analytics.com",
        "subject": "Monthly Analytics Report",
        "content": "Your monthly analytics report is ready. Key metrics show a 15% increase in user engagement.",
        "expected_triage": "respond",
        "category": "analytics_report",
        "expected_response": "Thank you for the monthly analytics report. The 15% increase in user engagement is excellent news. I'll review the full report and follow up if I have any questions."
    },
    {
        "id": 66,
        "sender": "legal@lawfirm.com",
        "subject": "Contract Review Complete",
        "content": "We've completed the review of the partnership agreement. A few minor changes are suggested.",
        "expected_triage": "notify_human",
        "category": "legal_review",
        "expected_response": ""
    },
    {
        "id": 67,
        "sender": "colleague@company.com",
        "subject": "Vacation Coverage Request",
        "content": "I'll be on vacation next week. Could you cover my client calls on Tuesday and Wednesday?",
        "expected_triage": "respond",
        "category": "vacation_coverage",
        "expected_response": "I'll cover your client calls on Tuesday and Wednesday while you're on vacation. Please send me any relevant notes or context."
    },
    {
        "id": 68,
        "sender": "research@competitor.com",
        "subject": "Industry Benchmarking Study",
        "content": "We're conducting an industry benchmarking study and would value your participation. Survey attached.",
        "expected_triage": "notify_human",
        "category": "benchmarking_study",
        "expected_response": ""
    },
    {
        "id": 69,
        "sender": "training@company.com",
        "subject": "New Employee Onboarding",
        "content": "Please complete the onboarding checklist for our new team member starting next Monday.",
        "expected_triage": "respond",
        "category": "onboarding_task",
        "expected_response": "I'll complete the onboarding checklist for the new team member. Everything should be ready by next Monday."
    },
    {
        "id": 70,
        "sender": "sponsor@charity.org",
        "subject": "Charity Event Sponsorship Opportunity",
        "content": "We're seeking sponsors for our annual charity gala. Your support would make a significant impact.",
        "expected_triage": "notify_human",
        "category": "charity_sponsorship",
        "expected_response": ""
    },
    {
        "id": 71,
        "sender": "colleague@company.com",
        "subject": "Resource Allocation Discussion",
        "content": "We need to discuss resource allocation for the next quarter. Can we set up a meeting?",
        "expected_triage": "respond",
        "category": "resource_planning",
        "expected_response": "We should discuss resource allocation. I'm available for a call this afternoon or Friday morning. Which works better for you?"
    },
    {
        "id": 72,
        "sender": "quality@company.com",
        "subject": "Quality Assurance Findings",
        "content": "The QA team has identified several issues in the latest release. Please review the attached report.",
        "expected_triage": "notify_human",
        "category": "quality_assurance",
        "expected_response": ""
    },
    {
        "id": 73,
        "sender": "freelancer@design.com",
        "subject": "Design Mockups Ready for Review",
        "content": "I've completed the initial design mockups for the new website. Please review and provide feedback.",
        "expected_triage": "respond",
        "category": "design_review",
        "expected_response": "Thank you for the design mockups. They look great overall. I have a few suggestions for the color scheme and layout which I've noted in the feedback document."
    },
    {
        "id": 74,
        "sender": "investor@vc.com",
        "subject": "Follow-up on Investment Discussion",
        "content": "Following our recent meeting, I'd like to schedule a follow-up call to discuss next steps.",
        "expected_triage": "notify_human",
        "category": "investment_discussion",
        "expected_response": ""
    },
    {
        "id": 75,
        "sender": "colleague@company.com",
        "subject": "Cross-team Collaboration Proposal",
        "content": "I think our teams could benefit from collaborating on the upcoming project. What are your thoughts?",
        "expected_triage": "respond",
        "category": "cross_team_collaboration",
        "expected_response": "I agree that cross-team collaboration would be beneficial for this project. Let's schedule a brief meeting to discuss how we can work together effectively."
    },
    {
        "id": 76,
        "sender": "support@software.com",
        "subject": "Bug Report Resolution",
        "content": "The bug you reported has been fixed in version 2.1.4. Please update your installation.",
        "expected_triage": "respond",
        "category": "bug_resolution",
        "expected_response": "Thank you for fixing the bug. I'll update to version 2.1.4 and test the fix. Appreciate the quick resolution."
    },
    {
        "id": 77,
        "sender": "board@company.com",
        "subject": "Board Meeting Preparation",
        "content": "Please prepare the quarterly financial summary for the upcoming board meeting next Thursday.",
        "expected_triage": "notify_human",
        "category": "board_meeting_prep",
        "expected_response": ""
    },
    {
        "id": 78,
        "sender": "student@university.edu",
        "subject": "Research Collaboration Inquiry",
        "content": "I'm a graduate student interested in collaborating on research related to your company's AI initiatives.",
        "expected_triage": "notify_human",
        "category": "research_collaboration",
        "expected_response": ""
    },
    {
        "id": 79,
        "sender": "colleague@company.com",
        "subject": "Feedback on Recent Presentation",
        "content": "Great presentation yesterday! I had a few thoughts on how we could improve the delivery next time.",
        "expected_triage": "respond",
        "category": "presentation_feedback",
        "expected_response": "Thank you for the feedback on my presentation. I appreciate your suggestions for improvement. I'll incorporate them for future presentations."
    },
    {
        "id": 80,
        "sender": "procurement@company.com",
        "subject": "Vendor Selection Process",
        "content": "We're in the final stages of selecting a new vendor for our IT infrastructure. Your input is requested.",
        "expected_triage": "notify_human",
        "category": "vendor_selection",
        "expected_response": ""
    },
    {
        "id": 81,
        "sender": "colleague@company.com",
        "subject": "Project Timeline Adjustment",
        "content": "Due to resource constraints, we need to adjust the project timeline. Can we discuss alternatives?",
        "expected_triage": "respond",
        "category": "timeline_adjustment",
        "expected_response": "I understand the resource constraints. Let's discuss timeline alternatives. I'm available for a call this afternoon to explore options."
    },
    {
        "id": 82,
        "sender": "marketing@agency.com",
        "subject": "Campaign Performance Update",
        "content": "The Q4 marketing campaign has exceeded expectations with a 40% increase in lead generation.",
        "expected_triage": "respond",
        "category": "campaign_performance",
        "expected_response": "Excellent results on the Q4 campaign! The 40% increase in lead generation is impressive. Let's discuss how to replicate this success in Q1."
    },
    {
        "id": 83,
        "sender": "security@company.com",
        "subject": "Security Training Reminder",
        "content": "Annual security awareness training is now available. Completion is mandatory by the end of the month.",
        "expected_triage": "respond",
        "category": "security_training",
        "expected_response": "I'll complete the annual security awareness training before the end of the month. Thank you for the reminder."
    },
    {
        "id": 84,
        "sender": "client@startup.com",
        "subject": "Product Demo Feedback",
        "content": "Thank you for the product demo. We're impressed and would like to move forward with a pilot program.",
        "expected_triage": "notify_human",
        "category": "pilot_program_interest",
        "expected_response": ""
    },
    {
        "id": 85,
        "sender": "colleague@company.com",
        "subject": "Knowledge Base Article",
        "content": "I've written a new article for the internal knowledge base about the deployment process. Please review.",
        "expected_triage": "respond",
        "category": "knowledge_base_contribution",
        "expected_response": "Thank you for contributing to the knowledge base. I've reviewed the deployment process article and it looks comprehensive. I've added a few minor suggestions for clarity."
    },
    {
        "id": 86,
        "sender": "regulatory@agency.gov",
        "subject": "Compliance Documentation Request",
        "content": "Please submit the required compliance documentation for the new regulatory requirements by March 15th.",
        "expected_triage": "notify_human",
        "category": "regulatory_compliance",
        "expected_response": ""
    },
    {
        "id": 87,
        "sender": "colleague@company.com",
        "subject": "Team Lunch Coordination",
        "content": "Let's organize a team lunch to celebrate the successful project completion. What dates work for everyone?",
        "expected_triage": "respond",
        "category": "team_celebration",
        "expected_response": "Great idea to celebrate the project completion! I'm available next Wednesday or Thursday for a team lunch. Let me know what works best for the group."
    },
    {
        "id": 88,
        "sender": "consultant@firm.com",
        "subject": "Consulting Engagement Update",
        "content": "Our consulting engagement is progressing well. Here's the status update on deliverables.",
        "expected_triage": "respond",
        "category": "consulting_update",
        "expected_response": "Thank you for the consulting engagement update. The progress looks good. I have a few questions about the timeline for the remaining deliverables."
    },
    {
        "id": 89,
        "sender": "alumni@university.edu",
        "subject": "Alumni Network Event",
        "content": "You're invited to our annual alumni networking event. It would be great to see you there.",
        "expected_triage": "respond",
        "category": "alumni_event",
        "expected_response": "Thank you for the alumni networking event invitation. Unfortunately, I won't be able to attend this year, but I appreciate being included."
    },
    {
        "id": 90,
        "sender": "colleague@company.com",
        "subject": "Peer Recognition Nomination",
        "content": "I'd like to nominate you for this month's peer recognition award for your outstanding work on the client project.",
        "expected_triage": "respond",
        "category": "peer_recognition",
        "expected_response": "Thank you for nominating me for the peer recognition award. I'm honored by the nomination and appreciate your recognition of my work."
    },
    {
        "id": 91,
        "sender": "supplier@materials.com",
        "subject": "Material Shortage Alert",
        "content": "Due to supply chain disruptions, we're experiencing shortages of key materials. Delivery delays expected.",
        "expected_triage": "notify_human",
        "category": "supply_shortage",
        "expected_response": ""
    },
    {
        "id": 92,
        "sender": "colleague@company.com",
        "subject": "Process Improvement Suggestion",
        "content": "I've been thinking about ways to improve our code review process. Here are my suggestions.",
        "expected_triage": "respond",
        "category": "process_improvement",
        "expected_response": "Thank you for your thoughtful suggestions on improving the code review process. I agree with several of your points. Let's discuss implementing these changes in our next team meeting."
    },
    {
        "id": 93,
        "sender": "customer@enterprise.com",
        "subject": "Reference Request",
        "content": "We're in the process of selecting a new vendor and would appreciate a reference for your services.",
        "expected_triage": "notify_human",
        "category": "reference_request",
        "expected_response": ""
    },
    {
        "id": 94,
        "sender": "colleague@company.com",
        "subject": "Work From Home Policy Discussion",
        "content": "The company is reviewing the work from home policy. I'd like to hear your thoughts on the current guidelines.",
        "expected_triage": "respond",
        "category": "policy_discussion",
        "expected_response": "I appreciate you asking for my input on the work from home policy. Overall, I think the current guidelines work well, but I have a few suggestions for improvement."
    },
    {
        "id": 95,
        "sender": "training@platform.com",
        "subject": "Certification Course Completion",
        "content": "Congratulations! You've successfully completed the Advanced Project Management certification course.",
        "expected_triage": "respond",
        "category": "certification_completion",
        "expected_response": "Thank you for the certification completion confirmation. I'm excited to have completed the Advanced Project Management course and look forward to applying these skills."
    },
    {
        "id": 96,
        "sender": "colleague@company.com",
        "subject": "Office Space Reorganization",
        "content": "We're reorganizing the office space to accommodate the growing team. Please indicate your space preferences.",
        "expected_triage": "respond",
        "category": "office_reorganization",
        "expected_response": "I've submitted my space preferences for the office reorganization. I prefer a quiet area near the windows if available."
    },
    {
        "id": 97,
        "sender": "partner@techalliance.com",
        "subject": "Technology Partnership Update",
        "content": "Our technology partnership is yielding excellent results. Let's discuss expansion opportunities.",
        "expected_triage": "notify_human",
        "category": "partnership_expansion",
        "expected_response": ""
    },
    {
        "id": 98,
        "sender": "colleague@company.com",
        "subject": "Skill Development Opportunity",
        "content": "There's an interesting workshop on machine learning next month. Would you be interested in attending together?",
        "expected_triage": "respond",
        "category": "skill_development",
        "expected_response": "That machine learning workshop sounds valuable. I'd be interested in attending together. Let's coordinate our schedules and registration."
    },
    {
        "id": 99,
        "sender": "client@corporation.com",
        "subject": "Contract Amendment Request",
        "content": "We'd like to discuss amending the current contract to include additional services. Please review the proposed changes.",
        "expected_triage": "notify_human",
        "category": "contract_amendment",
        "expected_response": ""
    },
    {
        "id": 100,
        "sender": "colleague@company.com",
        "subject": "End of Year Review Preparation",
        "content": "Let's start preparing for your end of year performance review. What accomplishments would you like to highlight?",
        "expected_triage": "respond",
        "category": "year_end_review",
        "expected_response": "Good idea to start preparing for the end of year review. I'd like to highlight the successful project delivery, the process improvements I implemented, and the team mentoring I did. Let's schedule time to discuss this in detail."
    }
]

def save_golden_dataset():
    """Save the golden dataset to a JSON file"""
    with open('golden_dataset.json', 'w') as f:
        json.dump(GOLDEN_EMAILS, f, indent=2)
    print(f"Saved {len(GOLDEN_EMAILS)} emails to golden_dataset.json")

def get_golden_emails() -> List[Dict]:
    """Get the golden dataset"""
    return GOLDEN_EMAILS

if __name__ == "__main__":
    save_golden_dataset()
    
    # Print summary
    categories = {}
    for email in GOLDEN_EMAILS:
        triage = email["expected_triage"]
        categories[triage] = categories.get(triage, 0) + 1
    
    print("\nDataset Summary:")
    for category, count in categories.items():
        print(f"  {category}: {count} emails")