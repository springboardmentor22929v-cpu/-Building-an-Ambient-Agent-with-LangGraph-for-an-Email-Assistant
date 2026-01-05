import re
from typing import Dict, Tuple

SPAM_PATTERNS = re.compile(r"unsubscribe|buy now|free money|lottery|click here|limited time offer|save 50%", re.I)
SCHEDULE_PATTERNS = re.compile(r"meeting|schedule|calendar|invite|reschedule|availability|book|appointment|kickoff", re.I)
LEGAL_BILLING_PATTERNS = re.compile(r"invoice|billing|contract|legal|terms|payment|receipt", re.I)
REQUEST_PATTERNS = re.compile(r"\b(can you|could you|please|would you|help|do you mind|how do i)\b", re.I)


def triage_email(email: Dict) -> Tuple[str, str]:
    """Return (classification, reasoning). Classification is one of: ignore, notify_human, respond."""
    text = f"{email.get('subject','')} {email.get('body','')}".lower()

    if SPAM_PATTERNS.search(text):
        return 'ignore', 'Contains spam/unsubscribe/marketing keywords'

    if SCHEDULE_PATTERNS.search(text) or LEGAL_BILLING_PATTERNS.search(text):
        return 'notify_human', 'Detected scheduling / billing / legal keywords'

    if REQUEST_PATTERNS.search(text) or '?' in text:
        return 'respond', 'Detected request-like phrasing or question mark'

    # Default conservative behavior
    return 'notify_human', 'No strong heuristic match; escalate to human'


# LLM-backed classifier (calls src_py.llm) with safe fallback
def triage_email_with_llm(email: Dict) -> Tuple[str, str]:
    """
    Try to classify using an LLM (Gemini). If the LLM integration is not
    available or an error occurs, fall back to the local `triage_email`.
    """
    try:
        # Try first non-relative import (works when running as script)
        from llm import classify_email_with_llm
    except Exception:
        try:
            # Try package-relative import (works when run as a module)
            from .llm import classify_email_with_llm
        except Exception:
            return triage_email(email)

    try:
        return classify_email_with_llm(email)
    except Exception:
        return triage_email(email)
