import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
import resend
import time
import logging
import re
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import random

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

EVENT_NAME = os.getenv("EVENT_NAME")
EVENT_DATE = os.getenv("EVENT_DATE")
EVENT_LOCATION = os.getenv("EVENT_LOCATION")
EVENT_REGISTER_URL = os.getenv("EVENT_REGISTER_URL", "https://yourdomain.com/register")
UNSUBSCRIBE_BASE_URL = os.getenv("UNSUBSCRIBE_BASE_URL", "https://yourdomain.com/unsubscribe")

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "events@mariageni.se")
RATE_LIMIT_DELAY = int(os.getenv("RATE_LIMIT_DELAY", "2"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# Initialize Groq & Resend
groq_client = Groq(api_key=GROQ_API_KEY)
resend.api_key = RESEND_API_KEY

# Setup logging
log_filename = f'logs/email_campaign_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)


def is_valid_email(email):
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_csv(df):
    """Validate CSV has required columns and valid emails."""
    required_columns = ['full_name', 'email', 'company', 'job_title', 'industry', 'goal', 'interests']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logging.error(f"Missing required columns: {missing_columns}")
        raise ValueError(f"CSV missing columns: {missing_columns}")
    
    # Validate emails
    invalid_emails = []
    for idx, row in df.iterrows():
        if not is_valid_email(row['email']):
            invalid_emails.append(row['email'])
            logging.warning(f"Invalid email format: {row['email']} for {row['full_name']}")
    
    if invalid_emails:
        logging.warning(f"Found {len(invalid_emails)} invalid emails. These will be skipped.")
    
    return df[df['email'].apply(is_valid_email)]


def get_subject_line(variant=None):
    """Generate subject line with A/B testing variants."""
    subjects = [
        f"You're Invited: {EVENT_NAME}",
        f"Join us at {EVENT_NAME}",
        f"Exclusive Invitation: {EVENT_NAME}"
    ]
    
    if variant is None:
        variant = random.randint(0, 2)
    
    return subjects[variant], variant


def minimal_html_wrap(text, recipient_email):
    """
    Convert plain text to minimal HTML with unsubscribe link.
    """
    unsubscribe_link = f"{UNSUBSCRIBE_BASE_URL}?email={recipient_email}"
    html_text = text.replace("\n", "<br>")
    
    html = f"""<html>
<body>
{html_text}
<br><br>
<p style="font-size:11px;color:#888;">
If you wish to unsubscribe, <a href="{unsubscribe_link}">click here</a>.
</p>
</body>
</html>"""
    
    return html


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_invitation(profile):
    """
    Generate a natural, human-like personalized email with retry logic.
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
    - Length: 140-200 words
    - Sound warm and personal, NOT generic
    - Do NOT include: "Best regards", "Regards", signatures, brackets, placeholders
    - Do NOT include [Your Name]
    - End naturally, like a human email (e.g., short personal closing line)
    - No subject line
    """

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Write human-like emails with natural tone."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.8
        )
        
        body = response.choices[0].message.content.strip()
        logging.info(f"Email generated for {profile['full_name']}")
        return body
    
    except Exception as e:
        logging.error(f"Failed to generate email for {profile['full_name']}: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def send_email(to_email, subject, html_body):
    """
    Send email through Resend API with retry logic.
    """
    if DRY_RUN:
        logging.info(f"[DRY RUN] Would send email to: {to_email}")
        logging.info(f"[DRY RUN] Subject: {subject}")
        return True
    
    try:
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": html_body
        })
        logging.info(f"Email sent successfully to: {to_email}")
        return True
    
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")
        raise


def save_generated_emails(emails_data):
    """Save generated emails to CSV as backup."""
    os.makedirs('output', exist_ok=True)
    filename = f'output/generated_emails_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    df = pd.DataFrame(emails_data)
    df.to_csv(filename, index=False)
    logging.info(f"Generated emails saved to: {filename}")
    return filename


def generate_report(stats):
    """Generate and save campaign report."""
    success_rate = (stats['sent'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    report = f"""
==========================================
EMAIL CAMPAIGN REPORT
==========================================
Campaign Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Event: {EVENT_NAME}

Total profiles: {stats['total']}
Valid emails: {stats['valid']}
Invalid emails: {stats['invalid']}

Successfully generated: {stats['generated']}
Successfully sent: {stats['sent']}
Failed: {stats['failed']}

Success rate: {success_rate:.2f}%
Dry run mode: {DRY_RUN}

Total execution time: {stats['duration']:.2f} seconds
==========================================
"""
    
    print(report)
    
    # Save report
    os.makedirs('reports', exist_ok=True)
    report_filename = f'reports/campaign_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    with open(report_filename, 'w') as f:
        f.write(report)
    
    logging.info(f"Report saved to: {report_filename}")
    return report


def main():
    start_time = time.time()
    
    csv_path = "data/4_profiles.csv"
    logging.info(f"Starting email campaign: {EVENT_NAME}")
    logging.info(f"Loading profiles from: {csv_path}")
    logging.info(f"Dry run mode: {DRY_RUN}")
    
    # Load and validate CSV
    try:
        profiles = pd.read_csv(csv_path)
        logging.info(f"Loaded {len(profiles)} profiles")
        
        profiles = validate_csv(profiles)
        logging.info(f"Validated {len(profiles)} profiles with valid emails")
    
    except Exception as e:
        logging.error(f"Failed to load/validate CSV: {e}")
        return
    
    # Statistics
    stats = {
        'total': len(pd.read_csv(csv_path)),
        'valid': len(profiles),
        'invalid': len(pd.read_csv(csv_path)) - len(profiles),
        'generated': 0,
        'sent': 0,
        'failed': 0,
        'duration': 0
    }
    
    # Storage for generated emails
    generated_emails_data = []
    
    print(f"\nProcessing {len(profiles)} profiles...\n")
    
    for i, profile in profiles.iterrows():
        print(f"[{i+1}/{len(profiles)}] Processing {profile['full_name']} ({profile['email']})")
        
        try:
            # Generate email body
            body = generate_invitation(profile)
            stats['generated'] += 1
            
            # Generate subject with A/B testing
            subject, variant = get_subject_line()
            logging.info(f"Using subject variant {variant} for {profile['email']}")
            
            # Wrap in HTML with unsubscribe link
            html_body = minimal_html_wrap(body, profile['email'])
            
            # Store generated email
            email_record = {
                'timestamp': datetime.now().isoformat(),
                'full_name': profile['full_name'],
                'email': profile['email'],
                'subject': subject,
                'subject_variant': variant,
                'body': body,
                'sent_status': 'pending',
                'error_message': None
            }
            
            # Send email
            try:
                send_email(profile['email'], subject, html_body)
                stats['sent'] += 1
                email_record['sent_status'] = 'sent'
                print(f"   Success: Email sent")
            
            except Exception as e:
                stats['failed'] += 1
                email_record['sent_status'] = 'failed'
                email_record['error_message'] = str(e)
                print(f"   Failed: {e}")
            
            generated_emails_data.append(email_record)
            
            # Rate limiting (don't delay after last email)
            if i < len(profiles) - 1:
                logging.info(f"Rate limiting: waiting {RATE_LIMIT_DELAY} seconds...")
                time.sleep(RATE_LIMIT_DELAY)
        
        except Exception as e:
            stats['failed'] += 1
            logging.error(f"Error processing {profile['full_name']}: {e}")
            print(f"   Error: {e}")
            
            generated_emails_data.append({
                'timestamp': datetime.now().isoformat(),
                'full_name': profile['full_name'],
                'email': profile['email'],
                'subject': None,
                'subject_variant': None,
                'body': None,
                'sent_status': 'failed',
                'error_message': str(e)
            })
    
    # Save backup
    if generated_emails_data:
        backup_file = save_generated_emails(generated_emails_data)
        print(f"\nBackup saved: {backup_file}")
    
    # Generate report
    stats['duration'] = time.time() - start_time
    generate_report(stats)
    
    logging.info("Campaign completed")


if __name__ == "__main__":
    main()