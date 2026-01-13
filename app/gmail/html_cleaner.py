from bs4 import BeautifulSoup
import re


def clean_html(html_content: str) -> str:
    """
    Convert HTML email content into clean, readable plain text.
    Preserves paragraph structure while removing junk.
    """

    # Parse HTML safely
    soup = BeautifulSoup(html_content, "lxml")

    # Remove non-text elements
    for tag in soup(["script", "style", "img", "svg"]):
        tag.decompose()

    # Extract visible text
    text = soup.get_text(separator="\n")

    # Remove invisible / tracking unicode characters
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", text)

    # Normalize spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive newlines (keep paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
