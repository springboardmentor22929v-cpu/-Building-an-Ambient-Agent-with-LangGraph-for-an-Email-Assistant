import base64
from app.gmail.html_cleaner import clean_html


def extract_email_body(payload):
    texts = []

    if "parts" in payload:
        for part in payload["parts"]:
            mime = part.get("mimeType", "")
            data = part.get("body", {}).get("data")

            if data:
                decoded = base64.urlsafe_b64decode(
                    data
                ).decode("utf-8", errors="ignore")

                if mime == "text/plain":
                    texts.append(decoded)

                elif mime == "text/html":
                    texts.append(clean_html(decoded))

            # recurse safely
            if "parts" in part:
                nested = extract_email_body(part)
                if nested:
                    texts.append(nested)

    else:
        data = payload.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(
                data
            ).decode("utf-8", errors="ignore")
            texts.append(clean_html(decoded))

    # join all meaningful text
    final_text = "\n".join(t.strip() for t in texts if t.strip())

    return final_text if final_text else "No readable content"
