from app.gmail.read_emails import read_latest_emails

emails = read_latest_emails(10)

for i, email in enumerate(emails, 1):
    print(f"\nEmail {i}")
    print("Subject:", email["subject"])
    print("Body:", email["body"][:300])
