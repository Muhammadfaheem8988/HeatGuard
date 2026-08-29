import requests, json

# Socrata uses dollar-sign params: , , etc.
print("=== CDC PLACES correct Socrata SoQL ===")
url = "https://chronicdata.cdc.gov/resource/cwsq-ngmh.json?" + "%24limit=3&StateAbbr=AZ&Year=2022"
r = requests.get(url, timeout=30)
print(f"Status: {r.status_code}")
print(f"First 500: {r.text[:500]}")

print()
# Use requests params dict which handles encoding
params = {
    "StateAbbr": "AZ",
    "Year": "2022",
}
r2 = requests.get("https://chronicdata.cdc.gov/resource/cwsq-ngmh.json", params=params, timeout=30)
print(f"Attempt 2 Status: {r2.status_code}")
print(f"URL: {r2.url[:120]}")
if r2.ok:
    d = r2.json()
    print(f"Records: {len(d)}")
    if d:
        print(f"Keys: {list(d[0].keys())}")
        print(f"Sample: {json.dumps(d[0], indent=2)[:600]}")
else:
    print(f"Error: {r2.text[:300]}")