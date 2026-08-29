import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# List available models
r = requests.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    params={"key": GEMINI_API_KEY},
    timeout=15
)
print("Status:", r.status_code)
if r.ok:
    models = r.json().get("models", [])
    for m in models:
        name = m.get("name","")
        supported = m.get("supportedGenerationMethods", [])
        if "generateContent" in supported:
            print(f"  {name}")