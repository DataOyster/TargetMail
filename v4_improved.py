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


def is_unsubscribed(email):
    """Check if email is in unsubscribe list."""
    unsubscribe_file = "data/unsubscribed.csv"
    
    if not os.path.exists(unsubscribe_file):
        return False
    
    try:
        unsubscribed = pd.read_csv(unsubscribe_file)
        return email in unsubscribed['email'].values
    except:
        return False


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


def get_subject_line(profile, variant=None):
    """Generate personalized subject line with A/B testing variants."""
    # Get first name for personalization
    name_first = profile['full_name'].split()[0]
    
    subjects = [
        f"{name_first}, you're invited to {EVENT_NAME}",
        f"Personal invitation for {name_first}: {EVENT_NAME}",
        f"{name_first} - Join us at {EVENT_NAME}"
    ]
    
    if variant is None:
        variant = random.randint(0, 2)
    
    return subjects[variant], variant


def minimal_html_wrap(text, recipient_email):
    """
    Convert plain text to minimal HTML with unsubscribe link.
    More natural formatting to avoid promotion folder.
    """
    unsubscribe_link = f"{UNSUBSCRIBE_BASE_URL}?email={recipient_email}"
    
    # Split into paragraphs for more natural formatting
    paragraphs = text.split('\n\n')
    html_paragraphs = ''.join([f'<p>{p.replace(chr(10), "<br>")}</p>' for p in paragraphs if p.strip()])
    
    html = f"""<html>
<body style="font-family:Arial,sans-serif;font-size:14px;color:#333;line-height:1.6;">
{html_paragraphs}
<p style="margin-top:30px;font-size:11px;color:#999;border-top:1px solid #eee;padding-top:10px;">
<a href="{unsubscribe_link}" style="color:#999;text-decoration:none;">Unsubscribe</a>
</p>
</body>
</html>"""
    
    return html


def generate_plain_text(text, recipient_email):
    """Generate plain text version of email."""
    unsubscribe_link = f"{UNSUBSCRIBE_BASE_URL}?email={recipient_email}"
    
    plain = f"""{text}

---
To unsubscribe, visit: {unsubscribe_link}
"""
    return plain


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_invitation(profile):
    """
    Generate a natural, human-like personalized email with retry logic.
    Enhanced prompt for better personalization and to avoid promotion folder.
    """
    prompt = f"""
You are writing a personal invitation email to a professional contact.

Event: {EVENT_NAME} on {EVENT_DATE} in {EVENT_LOCATION}

Recipient:
- Name: {profile['full_name']}
- Role: {profile['job_title']} at {profile['company']}
- Industry: {profile['industry']}
- Professional goal: {profile['goal']}
- Interests: {profile['interests']}

Write a warm, personal email (140-180 words) that:
1. Opens with a personalized greeting that references their specific role, company, or interests
2. Explains why THIS specific event would be valuable for THEM based on their goals and interests
3. Mentions 1-2 specific aspects of the event that align with their professional interests
4. Includes a clear but natural call-to-action about registering
5. Ends with a friendly, conversational closing (NOT "Best regards", "Sincerely", or formal signatures)
6. Sounds like it was written by a human colleague or friend, not a marketing department

Do NOT include:
- Subject line
- Formal signatures like "Best regards" or "Sincerely"
- [Placeholders] or brackets
- Generic corporate marketing language
- Heavy sales pitch or promotional tone
- Your name at the end

Write as if you're a real person genuinely inviting someone you know professionally.
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You write natural, personal emails that sound human and authentic, not corporate or promotional."},
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
def send_email(to_email, subject, html_body, plain_body):
    """
    Send email through Resend API with retry logic.
    Includes both HTML and plain text versions, plus List-Unsubscribe header.
    """
    if DRY_RUN:
        logging.info(f"[DRY RUN] Would send email to: {to_email}")
        logging.info(f"[DRY RUN] Subject: {subject}")
        return True
    
    try:
        # Extract unsubscribe URL from plain body
        unsubscribe_url = f"{UNSUBSCRIBE_BASE_URL}?email={to_email}"
        
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": html_body,
            "text": plain_body,
            "reply_to": SENDER_EMAIL,
            "headers": {
                "List-Unsubscribe": f"<{unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
            }
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
Unsubscribed: {stats['unsubscribed']}

Successfully generated: {stats['generated']}
Successfully sent: {stats['sent']}
Failed: {stats['failed']}

Success rate: {success_rate:.2f}%
Dry run mode: {DRY_RUN}

Total execution time: {stats['duration']:.2f} seconds
Average time per email: {stats['duration']/stats['valid']:.2f} seconds
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
        'unsubscribed': 0,
        'generated': 0,
        'sent': 0,
        'failed': 0,
        'duration': 0
    }
    
    # Storage for generated emails
    generated_emails_data = []
    
    print(f"\nProcessing {len(profiles)} profiles...\n")
    
    for i, profile in profiles.iterrows():
        # Check if unsubscribed
        if is_unsubscribed(profile['email']):
            logging.info(f"Skipping {profile['email']} - unsubscribed")
            stats['unsubscribed'] += 1
            continue
        
        print(f"[{i+1}/{len(profiles)}] Processing {profile['full_name']} ({profile['email']})")
        
        try:
            # Generate email body
            body = generate_invitation(profile)
            stats['generated'] += 1
            
            # Generate personalized subject with A/B testing
            subject, variant = get_subject_line(profile)
            logging.info(f"Using subject variant {variant} for {profile['email']}: {subject}")
            
            # Create both HTML and plain text versions
            html_body = minimal_html_wrap(body, profile['email'])
            plain_body = generate_plain_text(body, profile['email'])
            
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
            
            # Send email with both versions
            try:
                send_email(profile['email'], subject, html_body, plain_body)
                stats['sent'] += 1
                email_record['sent_status'] = 'sent'
                print(f"   Success: Email sent")
            
            except Exception as e:
                stats['failed'] += 1
                email_record['sent_status'] = 'failed'
                email_record['error_message'] = str(e)
                print(f"   Failed: {e}")
            
            generated_emails_data.append(email_record)
            
            # Rate limiting with random variation (more human-like)
            if i < len(profiles) - 1:
                # Random delay between base delay and base delay + 3 seconds
                delay = random.uniform(RATE_LIMIT_DELAY, RATE_LIMIT_DELAY + 3)
                logging.info(f"Rate limiting: waiting {delay:.1f} seconds...")
                time.sleep(delay)
        
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
    
    # Print deliverability tips
    print("\n" + "="*50)
    print("DELIVERABILITY TIPS:")
    print("="*50)
    print("1. Check that all DNS records (SPF, DKIM, DMARC) are verified in Resend")
    print("2. Start with small batches (10-20 emails) to warm up your domain")
    print("3. Ask initial recipients to move emails from Promotions to Primary")
    print("4. Encourage recipients to reply - this improves sender reputation")
    print("5. Monitor Resend dashboard for bounce rates and spam reports")
    print("6. Some emails may still land in Promotions - this is normal for event invites")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()