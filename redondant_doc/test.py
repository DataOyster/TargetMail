import os
import requests
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("targetmail_token")

print("=" * 60)
print("TEST CON MODELLO GRATUITO GARANTITO")
print("=" * 60)

if not HF_TOKEN:
    print("ERRORE: Token non trovato")
    exit(1)

print(f"✓ Token: {HF_TOKEN[:15]}...")

# MODELLO PICCOLO E GRATUITO - GPT-2 (sempre disponibile)
MODEL_ID = "gpt2"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

print(f"✓ Using model: {MODEL_ID}")
print(f"✓ URL: {API_URL}")

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# Test semplice
payload = {
    "inputs": "Write a professional email invitation: Dear",
    "parameters": {
        "max_new_tokens": 80,
        "temperature": 0.7,
        "return_full_text": False
    }
}

print("\n" + "=" * 60)
print("Sending request...")
print("=" * 60)

try:
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 503:
        print("\n⚠ Model is loading (cold start)")
        result = response.json()
        if "estimated_time" in result:
            print(f"Wait time: {result['estimated_time']} seconds")
            print("Try again in a moment!")
    elif response.status_code == 200:
        print("\n✓✓✓ SUCCESS! ✓✓✓")
        result = response.json()
        print(f"\nRaw response: {result}")
        
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get("generated_text", "")
            print(f"\n📧 GENERATED TEXT:\n{text}")
    else:
        print(f"\n✗ ERROR {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
except Exception as e:
    print(f"\n✗ EXCEPTION: {e}")

print("\n" + "=" * 60)
print("Se questo funziona, possiamo usare GPT-2 per le email!")
print("=" * 60)