import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HF_TOKEN = os.getenv("targetmail_token")

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# GUARANTEED WORKING MODEL
MODEL_URL = "https://router.huggingface.co/google/flan-t5-base"

def generate_email(profile):
    prompt = f"""
Write a professional and friendly email invitation for the person below.
Use natural English and avoid bullet points.

Name: {profile.get('name', '')}
Company: {profile.get('company', '')}
Job Title: {profile.get('job_title', '')}
Industry: {profile.get('industry', '')}
Focus Area: {profile.get('focus_area', '')}
"""

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 180}
    }

    response = requests.post(MODEL_URL, headers=headers, json=payload, timeout=40)

    if response.status_code != 200:
        return f"API error: {response.status_code} - {response.text}"

    output = response.json()

    if isinstance(output, list) and "generated_text" in output[0]:
        return output[0]["generated_text"].strip()

    return "No generated text returned."

def load_csv(csv_path):
    profiles = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            profiles.append(row)
    return profiles

def main():
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    if not csv_files:
        print("No CSV files found.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = os.path.join(OUTPUT_DIR, f"HF_data_{timestamp}.txt")

    with open(output_file, "w", encoding="utf-8") as out:
        for csv_file in csv_files:
            profiles = load_csv(os.path.join(DATA_DIR, csv_file))

            for profile in profiles:
                email = generate_email(profile)

                out.write("=" * 50 + "\n")
                out.write("EMAIL GENERATED FROM PROFILE\n")
                out.write("=" * 50 + "\n\n")
                out.write(email + "\n\n")

    print(f"Emails saved in: {output_file}")

if __name__ == "__main__":
    main()
