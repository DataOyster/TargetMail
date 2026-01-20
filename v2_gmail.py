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

# Gmail-friendly verified sender
SENDER_EMAIL = "events@mariageni.se"

# Initialize Groq & Resend
groq_client = Groq(api_key=GROQ_API_KEY)
resend.api_key = RESEND_API_KEY


def wrap_html_gmail(body_text):
    """
    Wrap email body in simple HTML tags to improve Gmail compatibility.
    """
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 15px; line-height: 1.5;">
        {body_text.replace("\n", "<br>")}
        <br><br>
        <p style='color:#555;'>Best regards,<br><b>ConnectIQ Team</b></p>
    </body>
    </html>
    """
    return html


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

    Requirements:
    - 150–220 words
    - Make it warm, engaging, and role-specific
    - No generic phrases
    - Do NOT include subject line
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

    return response.choices[0].message.content.strip()


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
    csv_path = "data/4_profiles.csv"
    print(f"Loading profiles from: {csv_path}")

    profiles = pd.read_csv(csv_path)
    print(f"Found {len(profiles)} profiles. Sending Gmail-friendly emails...\n")

    for i, profile in profiles.iterrows():
        print(f"[{i+1}/{len(profiles)}] Processing {profile['full_name']} ({profile['email']})")

        # Generate body
        body = generate_invitation(profile)

        # Wrap for Gmail compatibility
        html_body = wrap_html_gmail(body)

        # Subject
        subject = f"You're Invited: {EVENT_NAME}"

        # Send
        send_email(profile["email"], subject, html_body)


if __name__ == "__main__":
    main()
