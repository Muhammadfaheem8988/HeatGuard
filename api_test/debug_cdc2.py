import requests, json
from pathlib import Path

# Debug what we're getting with 
params = {
    "StateAbbr": "AZ",
    "countyfips": "04013",
    "Year": "2022",
}
params["\"] = "5000"
params["\"] = "0"

r = requests.get("https://chronicdata.cdc.gov/resource/cwsq-ngmh.json", params=params, timeout=60)
print(f"Status: {r.status_code}")
print(f"URL used: {r.url[:150]}")
print(f"Content type: {r.headers.get('Content-Type')}")
raw = r.json()
print(f"Type: {type(raw)}, Length: {len(raw) if isinstance(raw, list) else 'N/A'}")
if isinstance(raw, list) and raw:
    print(f"First item type: {type(raw[0])}")
    print(f"First item: {json.dumps(raw[0], indent=2)[:500] if isinstance(raw[0], dict) else raw[0][:200]}")
elif isinstance(raw, dict):
    print(f"Dict response: {json.dumps(raw)[:500]}")