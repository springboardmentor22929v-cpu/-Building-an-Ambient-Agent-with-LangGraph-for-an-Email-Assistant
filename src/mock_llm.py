class MockLLM:
    def classify(self, subject, body):
        text = (subject + " " + body).lower()

        ignore_keywords = [
            "newsletter", "unsubscribe", "promotion", "sale", "offer",
            "digest", "social", "no-reply", "marketing", "ads",
            "maintenance", "reset", "notification"
        ]

        notify_keywords = [
            "urgent", "immediately", "escalation", "error", "failed",
            "issue", "complaint", "downtime", "critical", "payment failed",
            "server down", "bug", "problem", "invoice", "financial report",
            "logs", "discrepancy", "unhappy client"
        ]

        respond_keywords = [
            "meeting", "schedule", "availability", "question", "feedback",
            "proposal", "deadline", "interview", "request", "follow up",
            "timeline", "confirm", "review"
        ]

        # Ignore newsletters/promotions
        if any(k in text for k in ignore_keywords):
            return "ignore"

        # Notify if urgent/problematic, unless there's a clear ask
        if any(k in text for k in notify_keywords):
            # Respond only if urgent AND contains a clear ask
            if "?" in text or "please" in text or any(k in text for k in respond_keywords):
                return "respond_or_act"
            return "notify_human"

        # Respond if clear ask
        if any(k in text for k in respond_keywords):
            return "respond_or_act"

        # Fallback: polite request or question
        if "?" in text or "please" in text:
            return "respond_or_act"

        # Default
        return "notify_human"

    def draft_reply(self, subject, sender):
        return (
            f"Subject: Re: {subject}\n"
            f"Hi {sender.split('@')[0].title()},\n\n"
            "Thanks for your email. I’ll get back to you shortly.\n\n"
            "Best regards,\nRahul"
        )
