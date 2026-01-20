import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
import resend

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

EVENT_NAME = os.getenv("EVENT_NAME")
EVENT_DATE = os.getenv("EVENT_DATE")
EVENT_LOCATION = os.getenv("EVENT_LOCATION")
SENDER_EMAIL = "events@mariageni.se"  # Your verified sender

# Initialize Groq API client
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize Resend API client
resend.api_key = RESEND_API_KEY


def generate_invitation(profile):
    """
    Creates a personalized invitation email using Groq LLM.
    """
    prompt = f"""
    You are a professional email writer. 
    Write a personalized, friendly, and professional conference invitation.

    Event name: {EVENT_NAME}
    Event date: {EVENT_DATE}
    Location: {EVENT_LOCATION}

    Profile data:
    Full name: {profile['full_name']}
    Company: {profile['company']}
    Job title: {profile['job_title']}
    Industry: {profile['industry']}
    Goal: {profile['goal']}
    Interests: {profile['interests']}

    The email must be:
    - 150–220 words
    - Personalized based on their role and goals
    - Engaging and positive
    - Contain a clear invitation to join

    Write only the email body. No subject line.
    """

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You craft high-quality professional emails."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )

    return response.choices[0].message.content


def send_email(to_email, subject, html_body):
    """
    Sends email through Resend API.
    """
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
    # Load CSV file
    csv_path = "data/4_profiles.csv"
    print(f"Loading profiles from: {csv_path}")

    profiles = pd.read_csv(csv_path)

    print(f"Found {len(profiles)} profiles. Starting generation...\n")

    for i, profile in profiles.iterrows():
        print(f"\n[{i+1}/{len(profiles)}] Processing: {profile['full_name']} ({profile['email']})")

        # Generate the email body with Groq
        email_body = generate_invitation(profile)

        # Subject line
        subject = f"You're Invited: {EVENT_NAME}"

        # Send email
        send_email(profile["email"], subject, email_body)


if __name__ == "__main__":
    main()
