import os
import requests
from dotenv import load_dotenv

print("=" * 60)
print("TEST HUGGINGFACE API CONNECTION")
print("=" * 60)

# Test 1: Load token
print("\n1. Loading token from .env...")
load_dotenv()
HF_TOKEN = os.getenv("targetmail_token")

if not HF_TOKEN:
    print("   ✗ ERRORE: Token non trovato!")
    exit(1)
else:
    print(f"   ✓ Token trovato: {HF_TOKEN[:15]}...")

# Test 2: Check token validity
print("\n2. Checking token validity...")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}
try:
    response = requests.get("https://huggingface.co/api/whoami-v2", headers=headers, timeout=10)
    if response.status_code == 200:
        user_info = response.json()
        print(f"   ✓ Token valido! User: {user_info.get('name', 'Unknown')}")
    else:
        print(f"   ✗ Token non valido: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"   ✗ Errore connessione: {e}")
    exit(1)

# Test 3: Try a simple model (faster than Mistral)
print("\n3. Testing API with a small model (gpt2)...")
test_url = "https://api-inference.huggingface.co/models/gpt2"

payload = {
    "inputs": "Hello, this is a test.",
    "parameters": {"max_new_tokens": 20},
    "options": {"wait_for_model": True}
}

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

print("   Sending request...")
try:
    response = requests.post(test_url, headers=headers, json=payload, timeout=30)
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✓ API funziona!")
        result = response.json()
        print(f"   Response preview: {str(result)[:100]}...")
    elif response.status_code == 503:
        print("   ⚠ Model is loading (503). This is normal for first request.")
        print(f"   Response: {response.text[:200]}")
    else:
        print(f"   ✗ Error: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("   ✗ Request timeout (30s)")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Try Mistral model
print("\n4. Testing Mistral model...")
mistral_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

payload = {
    "inputs": "Write a short email greeting.",
    "parameters": {"max_new_tokens": 50},
    "options": {"wait_for_model": True}
}

print("   Sending request to Mistral (may take 30-60 seconds)...")
try:
    response = requests.post(mistral_url, headers=headers, json=payload, timeout=90)
    print(f"   Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✓ Mistral API funziona!")
        result = response.json()
        print(f"   Response: {result}")
    elif response.status_code == 503:
        print("   ⚠ Model is loading. Check the estimated_time in response:")
        print(f"   {response.text[:300]}")
    else:
        print(f"   ✗ Error: {response.status_code}")
        print(f"   Response: {response.text[:300]}")
        
except requests.exceptions.Timeout:
    print("   ✗ Request timeout (90s)")
    print("   Il modello potrebbe essere troppo lento o non disponibile")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETATO")
print("=" * 60)