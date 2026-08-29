import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = "gemini-flash-lite-latest"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
body = {
    "contents": [{"parts": [{"text": "Say exactly: HEAT ALERT works. Nothing else."}]}],
    "generationConfig": {"maxOutputTokens": 50, "temperature": 0}
}
r = requests.post(url, headers=headers, json=body, timeout=10)
d = r.json()
parts = d["candidates"][0]["content"]["parts"]
print("Parts:")
for i, p in enumerate(parts):
    print(f"  Part {i}: keys={list(p.keys())}")
    print(f"    text={p.get('text','<NO TEXT>')[:100]}")
    print(f"    has_thoughtSignature={'thoughtSignature' in p}")
# The text and thoughtSignature are in the SAME part - we just need the text field
all_text = " ".join(p.get("text","") for p in parts if p.get("text","").strip()).strip()
print(f"\nFull text: '{all_text}'")