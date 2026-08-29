import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = "gemini-3.5-flash-lite"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

# Simulate all top-3 alerts
top3 = [
    {"geoid": "04013981000", "area": "SW Phoenix", "temp": 36.6, "hi": 44.5, "vuln": 0.954, "elderly": 63.9, "uninsured": 36.1, "utility": 37.9, "pop": 803},
    {"geoid": "04013106801", "area": "Central Phoenix", "temp": 36.3, "hi": 45.4, "vuln": 0.646, "elderly": 34.2, "uninsured": 28.5, "utility": 31.2, "pop": 4812},
    {"geoid": "04013106001", "area": "Downtown Phoenix", "temp": 36.5, "hi": 45.9, "vuln": 0.428, "elderly": 22.1, "uninsured": 24.8, "utility": 22.6, "pop": 2341},
]

headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}

for t in top3:
    prompt = f"""You are an emergency heat response coordinator for Phoenix, AZ.
Generate a concise, actionable SMS-style alert (max 3 sentences, plain English, no markdown)
for field teams about census tract {t['geoid']} ({t['area']} area).

Data for July 15, 2024:
- Average temperature: {t['temp']}C ({t['temp']*9/5+32:.0f}F)
- Peak heat index: {t['hi']}C ({t['hi']*9/5+32:.0f}F)
- Vulnerability score: {t['vuln']:.3f} / 1.0
- Elderly risk indicator: {t['elderly']}%
- Uninsured adults: {t['uninsured']}%
- Utility shut-off risk: {t['utility']}%
- Population: {t['pop']}

Format: HEAT ALERT | {t['area']} Tract {t['geoid'][-6:]}: [2-3 specific action sentences]."""

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 250, "temperature": 0.4}
    }
    r = requests.post(GEMINI_URL, headers=headers, json=body, timeout=15)
    if r.ok:
        data = r.json()
        parts = data["candidates"][0]["content"]["parts"]
        text = " ".join(p["text"] for p in parts if "text" in p and "thoughtSignature" not in p).strip()
        finish = data["candidates"][0].get("finishReason", "?")
        print(f"\n=== Tract {t['geoid']} ({t['area']}) [finish={finish}] ===")
        print(text)
    else:
        print(f"ERROR {t['geoid']}: {r.text[:200]}")