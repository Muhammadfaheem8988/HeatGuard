import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}

prompt = """You are an emergency heat response coordinator for Phoenix, AZ.
Generate a concise, actionable SMS-style alert (max 3 sentences, plain English, no markdown)
for field teams about census tract 04013981000 (SW Phoenix area).

Data for July 15, 2024:
- Average temperature: 36.6C (97.9F)
- Peak heat index: 44.5C (112.1F)
- Vulnerability score: 0.954 / 1.0 (CRITICAL - highest in county)
- Elderly risk: 63.9% of residents show high elderly heat vulnerability
- Uninsured adults: 36.1%
- Utility shut-off risk: 37.9% (many lack reliable AC)
- Population: 803

Format: HEAT ALERT | SW Phoenix Tract 981000: [2-3 specific action sentences with locations or actions]."""

body = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "maxOutputTokens": 200,
        "temperature": 0.4,
        "thinkingConfig": {"thinkingBudget": 0}
    }
}

r = requests.post(GEMINI_URL, headers=headers, json=body, timeout=20)
print("Status:", r.status_code)
if r.ok:
    data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    print("ALERT:")
    print(text)
    print("\nFinish reason:", data["candidates"][0].get("finishReason"))
    print("Tokens used:", data.get("usageMetadata",{}).get("totalTokenCount"))
else:
    print("Error:", r.text[:300])