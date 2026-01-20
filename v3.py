import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
import resend

# This version removes templates and signatures, uses minimal HTML, and relies on Groq to generate fully natural, human-like emails to improve deliverability.

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

EVENT_NAME = os.getenv("EVENT_NAME")
EVENT_DATE = os.getenv("EVENT_DATE")
EVENT_LOCATION = os.getenv("EVENT_LOCATION")

# Verified sender
SENDER_EMAIL = "events@mariageni.se"

# Initialize Groq & Resend
groq_client = Groq(api_key=GROQ_API_KEY)
resend.api_key = RESEND_API_KEY


def minimal_html_wrap(text):
    """
    Convert plain text to minimal HTML with <br>,
    WITHOUT adding templates or signatures.
    This keeps Gmail compatibility high without looking like a bulk email.
    """
    html_text = text.replace("\n", "<br>")
    return f"<html><body>{html_text}</body></html>"


def generate_invitation(profile):
    """
    Generate a natural, human-like personalized email.
    No signatures, no placeholders, no generic lines.
    """
    prompt = f"""
    You are an expert email writer.
    Write a personalized, natural-sounding invitation email (not formal corporate style).
    It must feel like a human wrote it.

    Event name: {EVENT_NAME}
    Event date: {EVENT_DATE}
    Location: {EVENT_LOCATION}

    Person:
    - Name: {profile['full_name']}
    - Company: {profile['company']}
    - Role: {profile['job_title']}
    - Industry: {profile['industry']}
    - Goal: {profile['goal']}
    - Interests: {profile['interests']}

    Rules:
    - Length: 140–200 words
    - Sound warm and personal, NOT generic
    - Do NOT include: "Best regards", "Regards", signatures, brackets, placeholders
    - Do NOT include [Your Name]
    - End naturally, like a human email (e.g., short personal closing line)
    - No subject line
    """

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Write human-like emails with natural tone."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.8
    )

    return response.choices[0].message.content.strip()


def send_email(to_email, subject, html_body):
    try:
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": html_body
        })
        print(f"✔ Email sent to: {to_email}")
    except Exception as e:
        print(f"✖ Failed to send email to {to_email}: {e}")


def main():
    csv_path = "data/4_profiles.csv"
    print(f"Loading profiles from: {csv_path}")

    profiles = pd.read_csv(csv_path)
    print(f"Found {len(profiles)} profiles. Sending improved Gmail-friendly emails...\n")

    for i, profile in profiles.iterrows():
        print(f"[{i+1}/{len(profiles)}] Processing {profile['full_name']} ({profile['email']})")

        # Generate pure-human-like email
        body = generate_invitation(profile)

        # Minimal HTML only
        html_body = minimal_html_wrap(body)

        subject = f"You're Invited: {EVENT_NAME}"

        send_email(profile["email"], subject, html_body)


if __name__ == "__main__":
    main()
