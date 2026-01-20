import os
from resend import Emails
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SENDER = "events@mariageni.se"
RECIPIENT = "fabiorubychef@gmail.com"

groq_client = Groq(api_key=GROQ_API_KEY)
Emails.api_key = RESEND_API_KEY

def generate_test_email():
    prompt = """
    Write a short, clean, professional test email.
    No marketing language.
    No links.
    No images.

    Subject: Test Delivery – TargetMail
    """

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content

def send_test_email(body):
    email = Emails.send({
        "from": SENDER,
        "to": RECIPIENT,
        "subject": "Test Delivery – TargetMail",
        "html": f"<p>{body}</p>"
    })
    print("📩 Email sent!")
    print(email)
    return email

def save_html(body):
    os.makedirs("output", exist_ok=True)
    path = "output/test_email.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"💾 HTML saved to {path}")

def main():
    print("🧪 Generating test email content...")
    html_body = generate_test_email()

    print("💾 Saving HTML locally...")
    save_html(html_body)

    print("📨 Sending test email to Gmail...")
    send_test_email(html_body)

if __name__ == "__main__":
    main()
