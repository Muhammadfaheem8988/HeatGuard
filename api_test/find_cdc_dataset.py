import requests, json

# CDC PLACES full dataset - try multiple dataset IDs
datasets = [
    "swc5-untb",   # PLACES Local Data 2023
    "i46a-9kgh",   # PLACES 2022
    "cwsq-ngmh",   # The one we've been using
    "3876-b7mg",   # Potential other ID
]

for ds in datasets:
    url = f"https://chronicdata.cdc.gov/resource/{ds}.json?StateAbbr=AZ&countyfips=04013&%24limit=5"
    r = requests.get(url, timeout=20)
    if r.ok:
        d = r.json()
        if isinstance(d, list) and d and isinstance(d[0], dict):
            measures = list(set(row.get("measureid","") for row in d))
            print(f"{ds}: OK, {len(d)} records, measures: {measures}")
        else:
            print(f"{ds}: OK but unexpected format: {str(d)[:100]}")
    else:
        print(f"{ds}: {r.status_code}")