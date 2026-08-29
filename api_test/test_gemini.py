import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
body = {
    "contents": [{"parts": [{"text": "Say exactly: GEMINI_WORKS"}]}],
    "generationConfig": {"maxOutputTokens": 10, "temperature": 0}
}

r = requests.post(GEMINI_URL, headers=headers, json=body, timeout=15)
print("Status:", r.status_code)
print("Response:", r.text[:500])