import requests, json

# CDC PLACES - correct Socrata SoQL format
# Dataset: cwsq-ngmh - must use ,  etc.
print("=== CDC PLACES - correct Socrata format ===")
url = "https://chronicdata.cdc.gov/resource/cwsq-ngmh.json?StateAbbr=AZ&Year=2022&Measure=Current+lack+of+health+insurance+among+adults+aged+18-64+years&limit=3"
r = requests.get(url, timeout=30)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:400]}")

# Check all field names with first record
print()
url2 = "https://chronicdata.cdc.gov/resource/cwsq-ngmh.json?limit=2"
r2 = requests.get(url2, timeout=30)
print(f"ALL FIELDS (first 2 records): Status {r2.status_code}")
if r2.ok:
    d = r2.json()
    if d:
        print(f"Keys: {list(d[0].keys())}")
        print(f"Sample: {json.dumps(d[0], indent=2)[:600]}")

# CORRECT SVI URL check
print()
print("=== SVI 2022 URL check ===")
for url_svi in [
    "https://svi.cdc.gov/Documents/Data/2022/csv/states/AZ_CDC_SVI_2022.csv",
    "https://svi.cdc.gov/Documents/Data/2022/csv/states_yr2/Arizona.csv",
    "https://svi.cdc.gov/data-and-tools-download.html",
]:
    r = requests.get(url_svi, timeout=15, allow_redirects=True)
    print(f"  {url_svi[:70]} -> {r.status_code}")