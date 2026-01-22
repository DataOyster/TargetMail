# TargetMail Installation Guide

Quick start guide to get TargetMail running from scratch.

## What is TargetMail?

TargetMail automatically creates personalized event invitation emails using AI and sends them to your recipient list. You provide a list of people (CSV file), event details, and API keys - the system does the rest.

## Prerequisites

You need:
- A computer with Python installed (Windows, Mac, or Linux)
- Two API keys (free accounts work):
  - Groq API key (for AI email generation)
  - Resend API key (for sending emails)
- A verified email domain (for Resend)
- A CSV file with your recipient list

## Step-by-Step Installation

### Step 1: Install Python

**Windows:**
1. Go to python.org/downloads
2. Download Python 3.10 or newer
3. Run installer, check "Add Python to PATH"
4. Click Install Now

**Mac:**
1. Open Terminal
2. Install Homebrew (if not installed): `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
3. Run: `brew install python`

**Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

Verify installation:
```bash
python --version
```
Should show Python 3.8 or higher.

### Step 2: Download TargetMail

**Option A: Git (Recommended)**
```bash
git clone <your-repo-url>
cd TargetMail
```

**Option B: Manual Download**
1. Download ZIP from repository
2. Extract to a folder
3. Open terminal/command prompt in that folder

### Step 3: Install Required Packages

Create virtual environment (recommended):
```bash
python -m venv venv
```

Activate virtual environment:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

Install packages:
```bash
pip install pandas python-dotenv groq resend tenacity
```

### Step 4: Get Groq API Keypy

1. Go to console.groq.com
2. Sign up or log in with your account
3. Click on "API Keys" in left menu
4. Click "Create API Key"
5. Give it a name (e.g., "TargetMail")
6. Copy the key (starts with "gsk_...")
7. Save it somewhere safe (you'll need it in Step 6)

### Step 5: Get Resend API Key and Verify Domain

**Get API Key:**
1. Go to resend.com
2. Sign up or log in
3. Go to "API Keys" section
4. Click "Create API Key"
5. Copy the key (starts with "re_...")
6. Save it somewhere safe

**Verify Your Domain:**
1. In Resend dashboard, go to "Domains"
2. Click "Add Domain"
3. Enter your domain (e.g., mariageni.se)
4. Resend will show you DNS records to add:
   - SPF record
   - DKIM record
   - DMARC record (optional)
5. Go to your domain registrar (where you bought your domain)
6. Add these DNS records
7. Wait 5-30 minutes for verification
8. Refresh Resend page - status should show "Verified"

**Don't have a domain?**
- You can use Resend's test domain for testing
- Or buy a cheap domain (Namecheap, Google Domains, etc.)

### Step 6: Create Configuration File

In the TargetMail folder, create a file named `.env` (exactly like that, with the dot):

**Windows:**
1. Open Notepad
2. Copy the content below
3. Save As → File name: `.env` → Save as type: "All Files"

**Mac/Linux:**
```bash
nano .env
```

**Content:**
```env
# API Keys
GROQ_API_KEY=paste_your_groq_key_here
RESEND_API_KEY=paste_your_resend_key_here

# Event Details
EVENT_NAME=AI Summit 2026
EVENT_DATE=March 15, 2026
EVENT_LOCATION=Stockholm, Sweden

# Email Settings
SENDER_EMAIL=events@yourdomain.com
RATE_LIMIT_DELAY=2
DRY_RUN=true
```

Replace:
- `paste_your_groq_key_here` with your actual Groq API key
- `paste_your_resend_key_here` with your actual Resend API key
- `AI Summit 2026` with your event name
- `March 15, 2026` with your event date
- `Stockholm, Sweden` with your event location
- `events@yourdomain.com` with your verified sender email

**Important:** Keep `DRY_RUN=true` for testing!

### Step 7: Prepare Your Recipient List

Create a folder named `data` in the TargetMail directory:
```bash
mkdir data
```

Create a file named `4_profiles.csv` inside the `data` folder with this format:
```csv
full_name,email,company,job_title,industry,goal,interests
John Doe,john@example.com,TechCorp,CTO,Technology,Network with AI experts,Machine Learning
Jane Smith,jane@example.com,DataInc,Data Scientist,Analytics,Learn new frameworks,Python
```

**Required columns** (must be exactly these names):
- full_name: Person's name
- email: Their email address
- company: Company name
- job_title: Their job title
- industry: Industry sector
- goal: What they want to achieve
- interests: Their professional interests

**Tips:**
- Use Excel or Google Sheets to create this
- Export as CSV
- Make sure all emails are valid
- Start with 3-5 test emails first

### Step 8: Test Run (Dry Run)

This will generate emails but NOT send them:
```bash
python v3.py
```

**What you'll see:**
```
2026-01-20 10:30:00 - INFO - Starting email campaign: AI Summit 2026
2026-01-20 10:30:00 - INFO - Loading profiles from: data/4_profiles.csv
2026-01-20 10:30:00 - INFO - Loaded 2 profiles
2026-01-20 10:30:00 - INFO - Validated 2 profiles with valid emails
2026-01-20 10:30:00 - INFO - Dry run mode: True

Processing 2 profiles...

[1/2] Processing John Doe (john@example.com)
2026-01-20 10:30:02 - INFO - Email generated for John Doe
2026-01-20 10:30:02 - INFO - Using subject variant 0 for john@example.com
2026-01-20 10:30:02 - INFO - [DRY RUN] Would send email to: john@example.com
   Success: Email sent
...

Backup saved: output/generated_emails_20260120_103005.csv

==========================================
EMAIL CAMPAIGN REPORT
==========================================
...
Success rate: 100.00%
Dry run mode: True
...
```

**Check the results:**
1. Go to `output` folder
2. Open the CSV file
3. Look at the `body` column - these are your generated emails
4. Make sure they look good!

### Step 9: Send Real Emails

When you're happy with the test results:

1. Edit `.env` file
2. Change `DRY_RUN=true` to `DRY_RUN=false`
3. Save the file
4. Run again:
```bash
python v3.py
```

Emails will now be sent for real!

## Quick Reference Commands

**Start the system:**
```bash
python v3.py
```

**Test without sending (dry run):**
Set in `.env`: `DRY_RUN=true`

**Send for real:**
Set in `.env`: `DRY_RUN=false`

**Check logs:**
Look in `logs/` folder

**Check generated emails:**
Look in `output/` folder

**Check campaign report:**
Look in `reports/` folder

## Common Problems and Solutions

**"ModuleNotFoundError: No module named 'groq'"**
- Solution: Run `pip install groq resend pandas python-dotenv tenacity`

**"FileNotFoundError: data/4_profiles.csv"**
- Solution: Create `data` folder and put your CSV file there
- Make sure it's named exactly `4_profiles.csv`

**"Invalid email format" warnings**
- Solution: Fix the email addresses in your CSV
- Format must be: name@domain.com

**Emails not sending**
- Check: Is `DRY_RUN=false` in `.env`?
- Check: Is your domain verified in Resend?
- Check: Are your API keys correct?
- Check: Do you have internet connection?

**"Groq API error"**
- Check: Is your Groq API key correct in `.env`?
- Check: Do you have quota left on Groq account?

**"Resend API error"**
- Check: Is your Resend API key correct in `.env`?
- Check: Is sender email verified?
- Check: Do you have quota left? (3,000 emails/month free)

**Emails go to spam**
- Make sure domain is fully verified (SPF, DKIM, DMARC)
- Start with small batches (10-20 emails)
- Use your verified sender domain

## File Structure Overview

After installation, you should have:
```
TargetMail/
├── data/
│   └── 4_profiles.csv          (your recipient list)
├── logs/                        (created automatically)
├── output/                      (created automatically)
├── reports/                     (created automatically)
├── venv/                        (if you used virtual environment)
├── .env                         (your configuration - keep secret!)
├── v3.py                        (the main program)
└── README.md                    (documentation)
```

## What Happens When You Run It

1. System loads your `.env` configuration
2. Reads `data/4_profiles.csv`
3. Validates all email addresses
4. For each person:
   - AI generates personalized email
   - Adds unsubscribe link
   - Sends email (if not dry run)
   - Waits 2 seconds (rate limiting)
5. Saves everything to `output/` folder
6. Creates detailed log in `logs/` folder
7. Generates summary report in `reports/` folder

## Next Steps

**After successful test:**
1. Add more recipients to your CSV
2. Adjust event details in `.env` if needed
3. Run with `DRY_RUN=false` to send real emails

**Monitor results:**
- Check `logs/` for any errors
- Check Resend dashboard for delivery status
- Look at `reports/` for campaign statistics

**Tips for success:**
- Start with small batches (10-20 emails)
- Send to yourself first
- Check spam folder
- Monitor delivery rates
- Increase rate limit for large campaigns (change `RATE_LIMIT_DELAY` in `.env`)

## Getting Help

If you're stuck:
1. Check the error message in terminal
2. Look at the log file in `logs/` folder
3. Review this guide again
4. Check README.md for detailed information
5. Verify all API keys are correct
6. Make sure domain is verified

## Security Reminder

**Never share your `.env` file!**
- It contains your API keys
- Keep it private
- Don't upload to GitHub or share online
- Don't email it to anyone

## You're Ready!

That's it! You now have TargetMail installed and ready to use.

Remember to always test with `DRY_RUN=true` first!