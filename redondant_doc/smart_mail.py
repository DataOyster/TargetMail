import os
import json
import csv

# Path alla cartella con i profili
DATA_DIR = r"C:\Users\maria\OneDrive\Desktop\Fabio\TargetMail\data"
OUTPUT_DIR = os.path.join(os.path.dirname(DATA_DIR), "output")

# Crea la cartella output se non esiste
os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------
# Funzione per generare invito
# -------------------------
def generate_invite(profile):
    name = profile.get("name", "Colleague")
    company = profile.get("company", "")
    role = profile.get("job_title", "")

    conference_name = "ConnectIQ Future Networking Conference 2025"
    conference_date = "March 15, 2025"
    conference_location = "Stockholm Waterfront Congress Centre"

    context = ""
    if role and company:
        context = f"We believe your experience as {role} at {company} would make you an excellent participant in this edition."
    elif role:
        context = f"We believe your experience as {role} would make you an excellent participant in this edition."
    elif company:
        context = f"We believe your background at {company} would make you an excellent participant in this edition."

    email_text = f"""
Hi {name},

We are pleased to invite you to the upcoming {conference_name}, taking place on {conference_date} at {conference_location}.

This event brings together professionals, innovators and industry leaders for a day of high-value networking, insights, and strategic connections.

{context}

We hope to see you there!

Kind regards,
ConnectIQ Team
"""
    return email_text.strip()


# -------------------------
# Funzione per leggere file JSON
# -------------------------
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print(f"Skipping invalid JSON: {file_path}")
        return None


# -------------------------
# Funzione per leggere CSV
# -------------------------
def load_csv(file_path):
    profiles = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                profiles.append(row)
    except Exception:
        print(f"Skipping invalid CSV: {file_path}")
        return []
    return profiles


# -------------------------
# MAIN
# -------------------------
def main():

    if not os.path.isdir(DATA_DIR):
        print(f"Error: directory '{DATA_DIR}' not found.")
        return

    files = os.listdir(DATA_DIR)
    json_files = [f for f in files if f.endswith(".json")]
    csv_files = [f for f in files if f.endswith(".csv")]

    if not json_files and not csv_files:
        print("No JSON or CSV files found in the directory.")
        return

    print(f"Found {len(json_files)} JSON files and {len(csv_files)} CSV files.\n")

    # Processa JSON
    for file in json_files:
        file_path = os.path.join(DATA_DIR, file)
        profile = load_json(file_path)

        if not profile:
            continue

        email = generate_invite(profile)

        # Salva output in un txt
        output_file = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file)[0]}_email.txt")
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(email)

        print("="*60)
        print(f"EMAIL GENERATED FROM JSON: {file}")
        print("="*60)
        print(email, "\n\n")

    # Processa CSV
    for file in csv_files:
        file_path = os.path.join(DATA_DIR, file)
        profiles = load_csv(file_path)

        for i, profile in enumerate(profiles):
            email = generate_invite(profile)

            output_file = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file)[0]}_profile{i+1}.txt")
            with open(output_file, "w", encoding="utf-8") as out:
                out.write(email)

            print("="*60)
            print(f"EMAIL GENERATED FROM CSV: {file} (profile {i+1})")
            print("="*60)
            print(email, "\n\n")


if __name__ == "__main__":
    main()
