import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from resend import Emails

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("ORGANIZER_EMAIL")
EVENT_NAME = os.getenv("EVENT_NAME")
EVENT_DATE = os.getenv("EVENT_DATE")
EVENT_LOCATION = os.getenv("EVENT_LOCATION")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize Resend
Emails.api_key = RESEND_API_KEY


def generate_invite(profile):
    name = profile["full_name"]
    company = profile["company"]
    job = profile["job_title"]
    industry = profile["industry"]
    goal = profile["goal"]
    interests = profile["interests"]

    prompt = f"""
Write a complete, polished conference invitation email tailored to the recipient.
Do not leave placeholders. The email must include a subject line and a professional body.

Event Details:
Name: {EVENT_NAME}
Date: {EVENT_DATE}
Location: {EVENT_LOCATION}

Recipient Details:
Name: {name}
Company: {company}
Job Title: {job}
Industry: {industry}
Primary Goal: {goal}
Interests: {interests}

Write the email in natural, professional English, as if written by a high-level event organizer.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )

    # FIX: correct Groq message access
    email_text = response.choices[0].message.content
    return email_text


def extract_subject_and_body(text):
    """Extract subject and body from AI output."""
    lines = text.splitlines()
    subject = None

    for line in lines:
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            break

    if subject is None:
        subject = "Invitation to Upcoming Conference"

    body = text.replace(f"Subject: {subject}", "").strip()
    return subject, body


def send_email(recipient_email, subject, body):
    """Send the generated email using Resend."""
    Emails.send({
        "from": SENDER_EMAIL,
        "to": recipient_email,
        "subject": subject,
        "html": body
    })


def main():
    profiles_path = os.path.join("data", "4_profiles.csv")

    output_log = "output/send_log.txt"

    profiles = pd.read_csv(profiles_path)

    with open(output_log, "w", encoding="utf-8") as log:
        for index, profile in profiles.iterrows():

            full_name = profile["full_name"]
            email = profile["email"]

            print(f"Generating invitation for: {full_name} ({email})")

            ai_output = generate_invite(profile)
            subject, body = extract_subject_and_body(ai_output)

            print(f"Sending email to: {email}")
            send_email(email, subject, body)

            log.write(f"Sent to {email}: {subject}\n")

    print("All invitations sent successfully.")


if __name__ == "__main__":
    main()
