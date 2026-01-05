def archive_email(subject):
    return f"Archived: {subject}"

def notify_human(subject):
    return f"Flagged for review: {subject}"

def send_draft(draft):
    return f"Draft prepared:\n{draft}"