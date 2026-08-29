import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = "gemini-3.6-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}

# Simulate a real alert prompt for tract #1
prompt = """You are an emergency heat response coordinator for Phoenix, AZ.
Generate a concise, actionable SMS-style alert (max 3 sentences, plain English, no markdown)
for field teams about census tract 04013981000.

Data for July 15, 2024:
- Average temperature: 36.6C (97.9F)
- Peak heat index: 44.5C (112.1F)
- Vulnerability score: 0.954 / 1.0
- Elderly risk indicator: 63.9%
- Uninsured adults: 36.1%
- Utility shut-off risk: 37.9%
- Population: 803

Write the alert in the format: HEAT ALERT | [Area]: [2-3 action sentences]."""

body = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"maxOutputTokens": 150, "temperature": 0.4}
}

r = requests.post(GEMINI_URL, headers=headers, json=body, timeout=15)
print("Status:", r.status_code)
if r.ok:
    data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    print("ALERT TEXT:")
    print(text)
else:
    print("Error:", r.text[:300])