import os
import csv
import requests
import time
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


def generate_email(profile):
    """
    Uses Groq API (free!) to generate a professional email.
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
        "model": "llama-3.1-70b-versatile",  # Modello gratuito e potente
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

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            error_text = response.text[:300]
            return f"API error: {response.status_code} - {error_text}"

        data = response.json()
        
        # Extract email from response
        if "choices" in data and len(data["choices"]) > 0:
            email_text = data["choices"][0]["message"]["content"]
            return email_text.strip()
        
        return "No email generated"
        
    except requests.exceptions.Timeout:
        return "Error: Request timeout"
    except Exception as e:
        return f"Error: {str(e)}"


def load_csv_profiles(csv_path):
    """
    Loads profiles from a CSV file.
    """
    profiles = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            profiles.append(row)
    return profiles


def main():
    print("=" * 60)
    print("🚀 SMART MAIL GENERATOR - POWERED BY GROQ (FREE!)")
    print("=" * 60)
    
    # Find CSV files
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    if not csv_files:
        print(f"\n❌ No CSV files found in: {DATA_DIR}")
        return

    print(f"\n✓ Found {len(csv_files)} CSV file(s)")

    # Count total profiles
    total_profiles = 0
    for csv_file in csv_files:
        csv_path = os.path.join(DATA_DIR, csv_file)
        profiles = load_csv_profiles(csv_path)
        total_profiles += len(profiles)
    
    print(f"✓ Total profiles: {total_profiles}")
    
    # Calculate time estimate (30 req/min = 2 sec per request)
    estimated_time = (total_profiles * 2.5) / 60
    print(f"✓ Estimated time: ~{estimated_time:.1f} minutes")
    
    print("\n" + "=" * 60)
    response = input(f"Generate emails for {total_profiles} profiles? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    print("=" * 60)

    # Output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file_path = os.path.join(OUTPUT_DIR, f"emails_groq_{timestamp}.txt")

    processed = 0
    errors = 0
    
    start_time = time.time()
    
    with open(output_file_path, "w", encoding="utf-8") as out:
        out.write("=" * 60 + "\n")
        out.write("EMAIL GENERATION RESULTS - POWERED BY GROQ\n")
        out.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out.write("=" * 60 + "\n\n")
        
        for csv_file in csv_files:
            csv_path = os.path.join(DATA_DIR, csv_file)
            profiles = load_csv_profiles(csv_path)

            for profile in profiles:
                processed += 1
                name = profile.get('name', 'Unknown')
                
                print(f"\n[{processed}/{total_profiles}] {name}...", end=" ", flush=True)
                
                email = generate_email(profile)
                
                if "error" in email.lower() or "Error" in email:
                    errors += 1
                    print("❌ Error")
                else:
                    print("✓")

                # Write to file
                out.write("=" * 60 + "\n")
                out.write(f"EMAIL #{processed}\n")
                out.write("=" * 60 + "\n\n")
                out.write(f"Name: {name}\n")
                out.write(f"Company: {profile.get('company', 'N/A')}\n")
                out.write(f"Job Title: {profile.get('job_title', 'N/A')}\n\n")
                out.write(email + "\n\n")
                
                # Rate limiting: 30 req/min = wait 2 seconds between requests
                if processed < total_profiles:
                    time.sleep(2.1)

    elapsed_time = (time.time() - start_time) / 60
    
    print("\n" + "=" * 60)
    print(f"✅ COMPLETED in {elapsed_time:.1f} minutes!")
    print(f"   Processed: {processed} profiles")
    if errors > 0:
        print(f"   ⚠️  Errors: {errors}")
    print(f"\n📄 Results saved to:")
    print(f"   {output_file_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()