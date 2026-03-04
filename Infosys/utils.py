import re

def parse_email(email_dict: dict):
    """
    Extracts and cleans email components from the email dictionary.
    Returns: (author, to, subject, email_thread)
    """
    author = email_dict.get("author", "").strip()
    to = email_dict.get("to", "").strip()
    subject = email_dict.get("subject", "").strip()
    email_thread = email_dict.get("email_thread", "").strip()

    return author, to, subject, email_thread

def format_email_markdown(subject: str, author: str, to: str, email_thread: str):
    """
    Formats the email for a clean display in the console or UI.
    """
    return f"""
**From:** {author}
**To:** {to}
**Subject:** {subject}

---

{email_thread}
"""