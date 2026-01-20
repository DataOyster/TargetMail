# TargetMail v3 - AI-Powered Email Campaign System

## Overview

TargetMail is an automated email campaign system that generates and sends personalized event invitation emails using artificial intelligence. The system combines Groq's Llama 3.1 language model for content generation with Resend's email delivery infrastructure to create highly personalized, human-like invitation emails at scale.

## System Architecture

### Core Components

1. **Data Layer**
   - CSV-based profile storage
   - Profile validation and sanitization
   - Email address format verification
   - Automated backup generation

2. **AI Generation Layer**
   - Groq API integration (Llama 3.1-8b-instant model)
   - Context-aware prompt engineering
   - Personalization based on recipient profiles
   - Natural language email composition

3. **Email Delivery Layer**
   - Resend API integration
   - SMTP-compliant HTML formatting
   - Unsubscribe link injection
   - Delivery status tracking

4. **Control Systems**
   - Rate limiting engine
   - Retry logic with exponential backoff
   - A/B testing framework for subject lines
   - Dry run simulation mode

5. **Logging and Reporting**
   - Comprehensive operation logging
   - Campaign performance metrics
   - Error tracking and diagnostics
   - Automated report generation

### Data Flow
```
CSV Input → Validation → Profile Processing → AI Generation → HTML Formatting → 
Rate Limiter → Email Sending → Logging → Backup → Report Generation
```

## Technical Specifications

### Dependencies

- Python 3.8 or higher
- pandas: Data manipulation and CSV processing
- python-dotenv: Environment variable management
- groq: Groq API client library
- resend: Resend API client library
- tenacity: Retry logic implementation

### External Services

**Groq API**
- Service: LLM inference platform
- Model: llama-3.1-8b-instant
- Endpoint: https://api.groq.com/openai/v1/chat/completions
- Authentication: Bearer token
- Rate limits: Subject to Groq platform limits

**Resend API**
- Service: Transactional email delivery
- Endpoint: https://api.resend.com/emails
- Authentication: Bearer token
- Rate limits: Plan-dependent (3,000 emails/month free tier)

### Configuration Parameters

All configuration is managed through environment variables (.env file):

**Required:**
- GROQ_API_KEY: Groq platform API key
- RESEND_API_KEY: Resend platform API key
- EVENT_NAME: Event title for invitations
- EVENT_DATE: Event date (human-readable format)
- EVENT_LOCATION: Event location/venue

**Optional:**
- EVENT_REGISTER_URL: Event registration link (default: https://yourdomain.com/register)
- UNSUBSCRIBE_BASE_URL: Unsubscribe endpoint base URL (default: https://yourdomain.com/unsubscribe)
- SENDER_EMAIL: Verified sender email address (default: events@mariageni.se)
- RATE_LIMIT_DELAY: Delay between sends in seconds (default: 2)
- DRY_RUN: Enable test mode without actual sending (default: false)

### Input Data Schema

CSV file must contain the following columns (order independent):

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| full_name | string | Recipient's full name | "John Doe" |
| email | string | Valid email address | "john@example.com" |
| company | string | Company/organization name | "TechCorp" |
| job_title | string | Professional role/position | "CTO" |
| industry | string | Industry sector | "Technology" |
| goal | string | Professional objective | "Network with AI experts" |
| interests | string | Relevant skills/topics | "Machine Learning, Python" |

Email validation regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`

### AI Generation Parameters

**Groq API Request:**
```json
{
  "model": "llama-3.1-8b-instant",
  "messages": [
    {
      "role": "system",
      "content": "Write human-like emails with natural tone."
    },
    {
      "role": "user",
      "content": "[Personalized prompt with profile and event data]"
    }
  ],
  "max_tokens": 500,
  "temperature": 0.8
}
```

**Output Specifications:**
- Length: 140-200 words
- Tone: Warm, personal, conversational
- Style: Natural human writing (no formal signatures)
- No placeholders or template artifacts

### Email Formatting

**HTML Structure:**
```html
<html>
<body>
[AI-generated content with <br> for line breaks]
<br><br>
<p style="font-size:11px;color:#888;">
If you wish to unsubscribe, <a href="[unsubscribe_url]">click here</a>.
</p>
</body>
</html>
```

**Unsubscribe URL Format:**
```
{UNSUBSCRIBE_BASE_URL}?email={recipient_email}
```

### A/B Testing Framework

Three subject line variants are randomly assigned:
- Variant 0: "You're Invited: {EVENT_NAME}"
- Variant 1: "Join us at {EVENT_NAME}"
- Variant 2: "Exclusive Invitation: {EVENT_NAME}"

Distribution: Random uniform selection for each recipient
Tracking: Variant ID stored in backup CSV (subject_variant column)

### Retry Logic

Implemented using tenacity library with exponential backoff:

**Configuration:**
- Maximum attempts: 3
- Wait strategy: Exponential backoff
- Multiplier: 1
- Minimum wait: 2 seconds
- Maximum wait: 10 seconds

**Retry sequence:**
- Attempt 1: Immediate
- Attempt 2: ~2 seconds wait
- Attempt 3: ~4 seconds wait
- Attempt 4: ~8 seconds wait (if configured)

Applied to:
- AI email generation (generate_invitation)
- Email sending (send_email)

### Rate Limiting

**Implementation:**
- Delay applied between consecutive sends
- Configurable via RATE_LIMIT_DELAY environment variable
- No delay after final email in batch
- Uses time.sleep() for blocking delay

**Purpose:**
- Prevent API rate limit violations
- Improve sender reputation
- Distribute server load
- Comply with service provider policies

### Logging System

**Configuration:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email_campaign_YYYYMMDD_HHMMSS.log'),
        logging.StreamHandler()
    ]
)
```

**Log Levels:**
- INFO: Successful operations, status updates
- WARNING: Invalid emails, skipped profiles
- ERROR: Failed operations, exceptions

**Logged Events:**
- Campaign initialization
- CSV loading and validation
- Email generation success/failure
- Email sending success/failure
- Rate limiting delays
- Retry attempts
- Campaign completion

### Output Files

**Logs Directory (logs/):**
- Filename: email_campaign_YYYYMMDD_HHMMSS.log
- Format: Plain text with timestamps
- Content: All operations, errors, status updates
- Retention: Manual cleanup required

**Backup Directory (output/):**
- Filename: generated_emails_YYYYMMDD_HHMMSS.csv
- Format: CSV
- Columns: timestamp, full_name, email, subject, subject_variant, body, sent_status, error_message
- Purpose: Recovery, analysis, audit trail

**Reports Directory (reports/):**
- Filename: campaign_YYYYMMDD_HHMMSS.txt
- Format: Plain text
- Content: Campaign statistics and metrics
- Includes: Total counts, success rates, execution time

### Statistics and Metrics

Tracked metrics:
- total: Total profiles in input CSV
- valid: Profiles with valid email addresses
- invalid: Profiles with invalid email addresses
- generated: Emails successfully generated by AI
- sent: Emails successfully sent via Resend
- failed: Operations that failed after retries
- duration: Total execution time in seconds

Success rate calculation: (sent / total) * 100

### Dry Run Mode

When DRY_RUN=true:
- All validation executed normally
- AI email generation executed normally
- Email sending simulated (not actually sent)
- All logging and backup created
- Statistics calculated
- Report generated with dry run indicator

Purpose: Testing, validation, preview without actual delivery

### Error Handling

**CSV Validation Errors:**
- Missing required columns: Raises ValueError, logs error, exits
- Invalid email format: Logs warning, skips profile, continues

**API Errors:**
- Groq API failure: Retries up to 3 times, logs each attempt, marks as failed if all retries exhausted
- Resend API failure: Retries up to 3 times, logs each attempt, marks as failed if all retries exhausted

**File System Errors:**
- Missing directories: Auto-created (logs/, output/, reports/)
- Missing CSV: Logs error, exits
- File write errors: Logged but not fatal

### Security Considerations

**API Key Management:**
- Stored in .env file (not version controlled)
- Loaded via python-dotenv
- Never logged or printed
- Environment-based isolation

**Email Privacy:**
- Unsubscribe links include email parameter
- Email addresses logged (consider GDPR implications)
- No encryption of stored data (files are plain text)

**Injection Prevention:**
- Email validation prevents malformed addresses
- HTML escaping not implemented (AI-generated content assumed safe)
- No user input sanitization beyond email regex

## Performance Characteristics

**Processing Speed:**
- AI generation: ~1-2 seconds per email (Groq API dependent)
- Email sending: ~0.5-1 second per email (Resend API dependent)
- Rate limiting: Configurable delay (default 2 seconds)
- Total time: ~4-5 seconds per email (with default settings)

**Scalability:**
- Single-threaded execution (sequential processing)
- No parallel processing implemented
- Memory footprint: Low (streaming CSV processing with pandas)
- Suitable for: 10-1000 emails per campaign

**Bottlenecks:**
- API rate limits (primary constraint)
- Network latency
- Sequential processing design

## Compliance and Best Practices

**GDPR Compliance:**
- Unsubscribe links included in all emails
- Email addresses require recipient consent (not validated by system)
- Data retention: Manual cleanup required
- Right to be forgotten: Not automated

**CAN-SPAM Compliance:**
- Unsubscribe mechanism provided
- Sender identification via FROM address
- Subject lines not deceptive (event-based)

**Email Deliverability:**
- Minimal HTML reduces spam score
- Domain authentication required (SPF, DKIM, DMARC)
- Rate limiting improves sender reputation
- Unsubscribe compliance prevents blacklisting

## Limitations and Known Issues

**Current Limitations:**
- No parallel processing (sequential only)
- No email template customization (AI-generated only)
- No attachment support
- No rich HTML templates
- No recipient timezone handling
- No scheduling functionality
- No real-time analytics dashboard
- Unsubscribe handling not implemented (link provided but endpoint required)

**Known Issues:**
- Large CSV files (>10,000 rows) may cause memory issues
- Network failures during campaign cannot resume from checkpoint
- No duplicate email detection
- Subject line A/B test results not automatically analyzed

## Future Enhancement Opportunities

**High Priority:**
- Checkpoint/resume functionality for large campaigns
- Parallel processing with thread pool
- Real-time dashboard with progress tracking
- Unsubscribe endpoint implementation
- Duplicate email detection and prevention

**Medium Priority:**
- Custom email templates with AI content injection
- Recipient timezone-aware sending
- Campaign scheduling system
- A/B test result analysis and reporting
- Attachment support

**Low Priority:**
- Rich HTML template editor
- Multi-language support
- Integration with CRM systems
- Webhook support for delivery status
- Advanced analytics and reporting

## System Requirements

**Minimum:**
- Python 3.8+
- 512MB RAM
- 100MB disk space
- Internet connection

**Recommended:**
- Python 3.10+
- 1GB RAM
- 1GB disk space (for logs/backups)
- Stable internet connection (>1Mbps)

## License

MIT License

## Version

Current Version: 3.0
Release Date: January 2026