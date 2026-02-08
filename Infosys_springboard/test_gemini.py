'''from triage import triage_email

email = "Can you check my schedule for tomorrow?"

decision = triage_email(email)

print("Email:", email)
print("Triage decision:", decision)'''

from graph import app

result = app.invoke({
    "email": "Can you check my schedule for tomorrow?"
})

print(result)


