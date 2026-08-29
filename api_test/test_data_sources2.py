import requests, json
from pathlib import Path

# Strategy 1: Fix CDC PLACES query format (Socrata SoQL)
# Dataset: https://chronicdata.cdc.gov/resource/cwsq-ngmh
# Filter by StateAbbr=AZ and GeographyLevel=Census Tract

url1 = "https://chronicdata.cdc.gov/resource/cwsq-ngmh.json?StateAbbr=AZ&GeographyLevel=Census+Tract&Year=2022&limit=5"
print("CDC PLACES attempt 1:", url1[:80])
r = requests.get(url1, timeout=30)
print(f"  Status: {r.status_code}")
if r.ok:
    d = r.json()
    print(f"  Records: {len(d)}, Keys: {list(d[0].keys()) if d else 'empty'}")
    if d: print(f"  Sample: {json.dumps(d[0], indent=2)[:500]}")
else:
    print(f"  Error: {r.text[:200]}")

# Strategy 2: CDC SVI (Social Vulnerability Index) - no key, pre-computed scores
# https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html
# Available as direct download CSV
url2 = "https://svi.cdc.gov/Documents/Data/2022/csv/states/AZ_CDC_SVI_2022.csv"
print()
print("CDC SVI direct download attempt:", url2[:80])
r2 = requests.get(url2, timeout=30, stream=True)
print(f"  Status: {r2.status_code}")
print(f"  Content-Type: {r2.headers.get('Content-Type')}")
content_start = b""
for chunk in r2.iter_content(chunk_size=500):
    content_start = chunk
    break
print(f"  First bytes: {content_start[:200]}")

# Strategy 3: Census API with key=DEMO (some public APIs accept this)
url3 = "https://api.census.gov/data/2022/acs/acs5?get=NAME,B01001_001E&for=tract:*&in=state:04+county:013&key=DEMO"
print()
print("Census with key=DEMO:", url3[:80])
r3 = requests.get(url3, timeout=30)
print(f"  Status: {r3.status_code}, Content-Type: {r3.headers.get('Content-Type')}")
print(f"  First 200: {r3.text[:200]}")