from app.agent.triage import triage_email
from app.gmail.read_emails import read_latest_emails
from app.gmail.save_to_json import save_emails_to_json
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError


def main():
    print("📧 Fetching latest emails from Gmail...\n")

    # Step 1: Read emails (limit to avoid quota issues)
    emails = read_latest_emails(10)

    if not emails:
        print("No emails found.")
        return

    # Step 2: Save emails to JSON
    save_emails_to_json(emails)

    print("\n🔍 Running triage on fetched emails...\n")

    # Step 3: Classify EACH email (quota-safe)
    for idx, email in enumerate(emails, start=1):
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"

        print(f"📨 EMAIL {idx}:")
        MAX_CHARS = 600
        print(email_text[:MAX_CHARS])
        print("\n----------------------")

        state = {"email": email_text}

        try:
            state = triage_email(state)
            print("📌 TRIAGE DECISION:", state.get("decision"))

        except ChatGoogleGenerativeAIError:
            print("⚠️ Gemini quota exhausted. Stopping further triage.")
            break

        except Exception as e:
            print("⚠️ Unexpected error during triage:", str(e))
            break

        print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
