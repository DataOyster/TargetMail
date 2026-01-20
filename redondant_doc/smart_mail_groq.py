import os
import csv
import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("groq_api_key")

if not GROQ_API_KEY:
    print("=" * 60)
    print("⚠️  ERRORE: Chiave API Groq non trovata!")
    print("=" * 60)
    print("\n📝 Per ottenere una chiave API GRATUITA:")
    print("1. Vai su: https://console.groq.com/")
    print("2. Crea un account (gratuito)")
    print("3. Vai in 'API Keys'")
    print("4. Clicca 'Create API Key'")
    print("5. Aggiungi al file .env:")
    print("   groq_api_key=gsk_xxxxx")
    print("\n✅ COMPLETAMENTE GRATUITO!")
    print("   Limiti: 30 req/min, 14,400 req/giorno")
    print("=" * 60)
    exit(1)

print(f"✓ Groq API Key caricata: {GROQ_API_KEY[:20]}...")

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Groq API endpoint
API_URL = "https://api.groq.com/openai/v1/chat/completions"


def generate_email(profile, profile_num, total):
    """
    Uses Groq API (free!) to generate a professional email.
    Returns tuple: (success, email_text_or_error_message)
    """
    name = profile.get('name', 'Professional')
    company = profile.get('company', 'their company')
    job_title = profile.get('job_title', 'their role')
    industry = profile.get('industry', 'their industry')
    focus = profile.get('focus_area', 'their field')
    
    prompt = f"""Write a professional conference invitation email for:

Name: {name}
Company: {company}
Position: {job_title}
Industry: {industry}
Focus: {focus}

Write a warm, personalized 3-4 paragraph email invitation. No bullet points. Be engaging and professional."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional email writer. Write engaging, personalized conference invitation emails."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    print(f"\n[{profile_num}/{total}] Processing: {name}", flush=True)
    print(f"   Company: {company}", flush=True)
    print(f"   Sending request to Groq API...", end=" ", flush=True)

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        print(f"Status: {response.status_code}", flush=True)

        if response.status_code == 200:
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                email_text = data["choices"][0]["message"]["content"]
                print(f"   ✅ Email generated successfully ({len(email_text)} chars)", flush=True)
                return (True, email_text.strip())
            else:
                error_msg = "No choices in response"
                print(f"   ❌ {error_msg}", flush=True)
                return (False, f"Error: {error_msg}\nResponse: {json.dumps(data, indent=2)}")
        
        elif response.status_code == 429:
            error_msg = "Rate limit exceeded"
            print(f"   ⚠️  {error_msg} - Waiting 30 seconds...", flush=True)
            time.sleep(30)
            return (False, f"Error: {error_msg}")
        
        elif response.status_code == 401:
            error_msg = "Authentication failed - Check your API key"
            print(f"   ❌ {error_msg}", flush=True)
            return (False, f"Error: {error_msg}")
        
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', response.text[:200])
            except:
                error_msg = response.text[:200]
            
            print(f"   ❌ API Error: {error_msg}", flush=True)
            return (False, f"API Error ({response.status_code}): {error_msg}")
        
    except requests.exceptions.Timeout:
        error_msg = "Request timeout after 30 seconds"
        print(f"   ❌ {error_msg}", flush=True)
        return (False, f"Error: {error_msg}")
    
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"   ❌ {error_msg}", flush=True)
        return (False, f"Error: {error_msg}")
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"   ❌ {error_msg}", flush=True)
        return (False, f"Error: {error_msg}")


def load_csv_profiles(csv_path):
    """
    Loads profiles from a CSV file.
    """
    profiles = []
    print(f"\n📂 Loading CSV: {os.path.basename(csv_path)}", flush=True)
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            print(f"   Columns found: {', '.join(headers)}", flush=True)
            
            for row in reader:
                profiles.append(row)
        
        print(f"   ✅ Loaded {len(profiles)} profiles", flush=True)
    except Exception as e:
        print(f"   ❌ Error loading CSV: {str(e)}", flush=True)
        raise
    
    return profiles


def main():
    print("\n" + "=" * 60)
    print("🚀 SMART MAIL GENERATOR - POWERED BY GROQ (FREE!)")
    print("=" * 60)
    
    # Look for 5_profiles.csv specifically
    target_csv = "5_profiles.csv"
    csv_path = os.path.join(DATA_DIR, target_csv)
    
    if not os.path.exists(csv_path):
        print(f"\n❌ File not found: {csv_path}")
        print(f"\nPlease create a file named '{target_csv}' in the 'data' folder")
        print("Expected columns: name, company, job_title, industry, focus_area")
        return
    
    # Load profiles
    try:
        profiles = load_csv_profiles(csv_path)
    except Exception as e:
        print(f"\n❌ Failed to load profiles: {str(e)}")
        return
    
    if len(profiles) == 0:
        print("\n❌ No profiles found in CSV")
        return
    
    total_profiles = len(profiles)
    estimated_time = (total_profiles * 2.5) / 60
    
    print(f"\n📊 Summary:")
    print(f"   Total profiles: {total_profiles}")
    print(f"   Estimated time: ~{estimated_time:.1f} minutes")
    print(f"   Rate: ~2.5 seconds per email")
    
    print("\n" + "=" * 60)
    response = input(f"Generate emails for {total_profiles} profiles? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cancelled.")
        return
    
    print("=" * 60)
    print("\n🚀 Starting generation...\n")

    # Output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file_path = os.path.join(OUTPUT_DIR, f"emails_groq_{timestamp}.txt")

    processed = 0
    successful = 0
    errors = 0
    
    start_time = time.time()
    
    try:
        with open(output_file_path, "w", encoding="utf-8") as out:
            out.write("=" * 60 + "\n")
            out.write("EMAIL GENERATION RESULTS - POWERED BY GROQ\n")
            out.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out.write(f"Total Profiles: {total_profiles}\n")
            out.write("=" * 60 + "\n\n")
            
            for i, profile in enumerate(profiles, 1):
                name = profile.get('name', 'Unknown')
                
                success, result = generate_email(profile, i, total_profiles)
                
                processed += 1
                if success:
                    successful += 1
                else:
                    errors += 1

                # Write to file
                out.write("=" * 60 + "\n")
                out.write(f"EMAIL #{i}\n")
                out.write("=" * 60 + "\n\n")
                out.write(f"Name: {name}\n")
                out.write(f"Company: {profile.get('company', 'N/A')}\n")
                out.write(f"Job Title: {profile.get('job_title', 'N/A')}\n")
                out.write(f"Industry: {profile.get('industry', 'N/A')}\n")
                out.write(f"Focus Area: {profile.get('focus_area', 'N/A')}\n")
                out.write(f"Status: {'✅ SUCCESS' if success else '❌ ERROR'}\n\n")
                
                if success:
                    out.write("EMAIL:\n")
                    out.write("-" * 60 + "\n")
                    out.write(result + "\n\n")
                else:
                    out.write("ERROR DETAILS:\n")
                    out.write("-" * 60 + "\n")
                    out.write(result + "\n\n")
                
                # Flush to save progress
                out.flush()
                
                # Rate limiting: wait 2.1 seconds between requests
                if processed < total_profiles:
                    print(f"   ⏳ Waiting 2 seconds before next request...\n", flush=True)
                    time.sleep(2.1)

    except KeyboardInterrupt:
        print("\n\n⚠️  INTERRUPTED BY USER (Ctrl+C)")
        print(f"Progress saved up to profile #{processed}")
    
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {str(e)}")
        print(f"Progress saved up to profile #{processed}")
    
    elapsed_time = (time.time() - start_time) / 60
    
    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print("=" * 60)
    print(f"⏱️  Time elapsed: {elapsed_time:.1f} minutes")
    print(f"✅ Successful: {successful}/{total_profiles}")
    if errors > 0:
        print(f"❌ Errors: {errors}/{total_profiles}")
    print(f"\n📄 Results saved to:")
    print(f"   {output_file_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()