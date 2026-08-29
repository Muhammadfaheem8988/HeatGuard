import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Try gemini-3.5-flash-lite (lightweight, fast, non-thinking)
# and gemini-3.1-flash-lite as backup
for MODEL in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash"]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    body = {
        "contents": [{"parts": [{"text": "Reply with exactly: WORKS"}]}],
        "generationConfig": {"maxOutputTokens": 10, "temperature": 0}
    }
    r = requests.post(url, headers=headers, json=body, timeout=10)
    if r.ok:
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        print(f"{MODEL}: OK -> '{text.strip()}'")
        break
    else:
        print(f"{MODEL}: {r.status_code} - {r.json().get('error',{}).get('message','')[:80]}")