import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = "gemini-3.5-flash-lite"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}

prompt = """You are an emergency heat response coordinator for Phoenix, AZ.
Generate a concise, actionable SMS-style alert (max 3 sentences, plain English, no markdown)
for field teams about census tract 04013981000 (SW Phoenix).

Data for July 15, 2024:
- Average temperature: 36.6C (97.9F)
- Peak heat index: 44.5C (112.1F)
- Vulnerability score: 0.954 / 1.0 (CRITICAL)
- Elderly risk: 63.9%
- Uninsured adults: 36.1%
- Utility shut-off risk: 37.9%
- Population: 803

Format: HEAT ALERT | SW Phoenix Tract 981000: [2-3 action sentences]."""

body = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"maxOutputTokens": 400, "temperature": 0.4}
}

r = requests.post(url, headers=headers, json=body, timeout=30)
print("Status:", r.status_code)
d = r.json()
parts = d["candidates"][0]["content"]["parts"]
print("Parts count:", len(parts))
for i, p in enumerate(parts):
    keys = list(p.keys())
    print(f"  Part {i}: keys={keys}, has_thoughtSig={'thoughtSignature' in p}")
    if "text" in p:
        print(f"    text (first 200): {p['text'][:200]}")

# Apply the fixed extraction
final_parts = [p["text"] for p in parts if "text" in p and "thoughtSignature" not in p]
if not final_parts:
    final_parts = [p["text"] for p in parts if p.get("text","").strip()]
text = " ".join(final_parts).strip()
print(f"\nFINAL EXTRACTED TEXT:\n{text}")
print(f"\nfinishReason: {d['candidates'][0].get('finishReason')}")