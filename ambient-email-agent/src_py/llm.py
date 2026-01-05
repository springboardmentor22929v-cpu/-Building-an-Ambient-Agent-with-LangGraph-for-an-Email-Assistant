"""LLM integration layer (Gemini / Google Generative AI).

This module loads the API key from environment (via python-dotenv) and
provides a small wrapper `classify_email_with_llm` that asks the LLM to
triage an email. If the Gemini/Generative API or the SDK is unavailable,
it falls back to the local heuristic implementation in `triage.triage_email`.

To enable real Gemini usage, install `google-generativeai` and set
`GEMINI_API_KEY` in a `.env` file or system environment.
"""
from typing import Tuple, Dict

# NOTE: API key has been inlined per user request. Storing keys in source is
# insecure for production. Remove or rotate the key if this code is shared.
# Inserted API key (user provided):
GEMINI_API_KEY = "AIzaSyB9cfyARqDht__QGFDIm4S_BNQsyTt6Cp8"


def _call_gemini(prompt: str) -> str:
    """Attempt to call Google Generative AI / Gemini SDK if available.

    Returns the model text on success, or raises an exception.
    """
    try:
        import google.generativeai as genai
        # configure the SDK with the provided key
        genai.configure(api_key=GEMINI_API_KEY)
        # SDK naming may vary; this is a best-effort example call. Adjust
        # to your installed SDK version / method signatures.
        resp = genai.generate_text(model="text-bison-001", prompt=prompt)
        # Attempt common ways to get text
        if hasattr(resp, 'text'):
            return resp.text
        return str(resp)
    except Exception as e:
        raise


def classify_email_with_llm(email: Dict) -> Tuple[str, str]:
    """Return (classification, reasoning).

    Attempts to call the Gemini LLM. On any failure or if the API key is
    missing, falls back to the local `triage_email` heuristic.
    """
    prompt = (
        "You are an assistant that must classify incoming emails into exactly "
        "one of three labels: ignore, notify_human, respond. Provide a one-line "
        "reasoning after the classification.\n\n"
        f"Email subject: {email.get('subject','')}\n\n"
        f"Email body: {email.get('body','')}\n\n"
        "Return format (exactly):\nclassification: <ignore|notify_human|respond>\nreasoning: <one-line reasoning>"
    )

    if GEMINI_API_KEY:
        try:
            text = _call_gemini(prompt)
        except Exception:
            text = None
    else:
        text = None

    if text:
        # Parse a simple two-line response
        cls = None
        reasoning = ''
        for line in text.splitlines():
            if line.lower().strip().startswith('classification:'):
                cls = line.split(':', 1)[1].strip().lower()
            if line.lower().strip().startswith('reasoning:'):
                reasoning = line.split(':', 1)[1].strip()
        if cls in ('ignore', 'notify_human', 'respond'):
            return cls, reasoning or 'LLM provided classification'

    # Fallback to local heuristic to guarantee deterministic behavior
    try:
        # Import locally to avoid circular import at module level
        from triage import triage_email
    except Exception:
        # Try package-relative import (if code is run as module)
        from .triage import triage_email

    return triage_email(email)
