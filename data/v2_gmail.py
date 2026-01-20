import os
import pandas as pd
from groq import Groq
import resend
from dotenv import load_dotenv

load_dotenv()

# Load env variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

EVENT_NAME = os.getenv("EVENT_NAME")
EVENT_DATE = os.getenv("EVENT_DATE")
EVENT_LOCATION = os.getenv("EVENT_LOCATION")

# Gmail-friendly verified sender
SENDER_EMAIL = "events@mariageni.se"

# Initialize Groq & Resend
groq_client = Groq(api_key=GROQ_API_KEY)
resend.api_key = RESEND_API_KEY


def wrap_html_gmail(body_text):
    """Wrap email body in simple HTML tags to improve Gmail compatibility."""
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 15px; line-height: 1.5;">
        {body_text.replace("\n", "<br>")}
        <br><br>
        <p style="color:#555;">Best regards,<br><b>ConnectIQ Team</b></p>
    </body>
    </html>
    """
    return html


def generate_invitation(profile):
    """Generate personalized email body using Groq LLM."""
    full_name = profile["full_name"]
    job_title = profile["job_title"]
    industry = profile["industry"]
    interests = profile["interests"]
    goal = profile["goal"]

    prompt = f"""
You are an expert conference outreach writer.

Write a personalized invitation email BODY ONLY (no subject line) for:
Name: {full_name}
Role: {job_title}
Industry: {industry}
Interests: {interests}
Goal: {goal}

Event:
{EVENT_NAME} on {EVENT_DATE} at {EVENT_LOCATION}

Requirements:
- 150–220 words
- Warm, engaging, specific to their role and interests
- No generic phrases
- Do NOT include a subject line
- Do NOT add ANY signature
- Do NOT include placeholders like [Your Name]

End your answer after the last sentence of the body.  
The signature will be added automatically.
"""

    response = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message["content"]


def send_email(recipient_email, html_body):
    """Send email using Resend."""
    resend.Emails.send({
        "from": SENDER_EMAIL,
        "to": recipient_email,
        "subject": EVENT_NAME,
        "html": html_body,
    })


def main():
    csv_path = "data/4_profiles.csv"
    print(f"Loading profiles from: {csv_path}")

    profiles = pd.read_csv(csv_path)
    print(f"Found {len(profiles)} profiles. Sending Gmail-friendly emails...\n")

    for idx, profile in profiles.iterrows():
        full_name = profile["full_name"]
        email = profile["email"]
        print(f"[{idx+1}/{len(profiles)}] Processing: {full_name} ({email})")

        try:
            body = generate_invitation(profile)
            html = wrap_html_gmail(body)

            send_email(email, html)
            print(f"✓ Email sent to: {email}\n")

        except Exception as e:
            print(f"❌ Error sending to {email}: {e}\n")


if __name__ == "__main__":
    main()
