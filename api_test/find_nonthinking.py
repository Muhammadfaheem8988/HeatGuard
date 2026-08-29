import os
import requests, json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Try flash-lite with thinkingBudget=0, and also try gemini-flash-lite-latest
for MODEL, think_budget in [
    ("gemini-3.5-flash-lite", 0),
    ("gemini-flash-lite-latest", None),
    ("gemini-3.1-flash-lite", None),
]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    gen_cfg = {"maxOutputTokens": 100, "temperature": 0.3}
    if think_budget is not None:
        gen_cfg["thinkingConfig"] = {"thinkingBudget": think_budget}
    body = {
        "contents": [{"parts": [{"text": "Say: HEAT ALERT works"}]}],
        "generationConfig": gen_cfg
    }
    r = requests.post(url, headers=headers, json=body, timeout=10)
    if r.ok:
        d = r.json()
        parts = d["candidates"][0]["content"]["parts"]
        print(f"{MODEL} (budget={think_budget}): parts={[list(p.keys()) for p in parts]}")
        texts = [p.get("text","") for p in parts if "text" in p and "thoughtSignature" not in p]
        print(f"  text result: '{' '.join(texts).strip()}'")
    else:
        err = r.json().get("error",{}).get("message","")[:80]
        print(f"{MODEL}: ERROR {r.status_code} - {err}")