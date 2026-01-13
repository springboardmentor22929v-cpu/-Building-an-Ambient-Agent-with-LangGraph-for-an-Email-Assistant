import json
import os
from datetime import datetime


def save_emails_to_json(emails, file_path="data/gmail_emails.json"):
    """
    Save extracted Gmail emails to a JSON file
    """

    # Ensure data directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    payload = {
        "saved_at": datetime.utcnow().isoformat(),
        "email_count": len(emails),
        "emails": emails
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(emails)} emails to {file_path}")
