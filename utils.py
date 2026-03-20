def parse_email(email_text: str) -> dict:
    return {
        "raw": email_text,
        "summary": email_text[:100]
    }

def format_email_markdown(email_dict: dict) -> str:
    return f"### Email\n\n{email_dict['raw']}" 
