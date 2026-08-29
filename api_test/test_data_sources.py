import requests, json
from pathlib import Path

# CDC PLACES has tract-level health data including vulnerability indicators
# Dataset: cwsq-ngmh (2023 release)
# Try without key first - CDC PLACES uses Socrata API

# Query CDC PLACES for Arizona tracts (state FIPS 04)
# Key measures we want: ARTHRITIS, CASTHMA, CHD, etc.
# But more importantly: GHLTH, MHLTH (general health measures)
# CDC PLACES doesn't have poverty/age directly but has related health outcomes

# Let's try CDC PLACES first to see what's available for AZ
url_cdc = "https://chronicdata.cdc.gov/resource/cwsq-ngmh.json?locationabbr=AZ&year=2022&measureid=GHLTH&geographylevel=CensusTracts&limit=5"
print("Testing CDC PLACES API...")
r = requests.get(url_cdc, timeout=30)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Records: {len(data)}")
    if data:
        print(f"First record keys: {list(data[0].keys())}")
        print(f"First record: {json.dumps(data[0], indent=2)[:800]}")
else:
    print(f"Response: {r.text[:300]}")

# Also try Census API with key parameter (census.gov gives free keys)
# But for now let's check if just adding a dummy key helps
print()
print("Testing Census API without key but with user-agent header...")
url2 = "https://api.census.gov/data/2022/acs/acs5?get=NAME,B01001_001E&for=tract:*&in=state:04+county:013"
headers = {"User-Agent": "HeatGuard-Hackathon/1.0 (team@hackathon.com)"}
r2 = requests.get(url2, timeout=30, headers=headers)
print(f"Status: {r2.status_code}, Content-Type: {r2.headers.get('Content-Type')}")
print(f"First 200: {r2.text[:200]}")