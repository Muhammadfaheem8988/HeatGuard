import requests, json
from pathlib import Path

# Get all unique measures available for Maricopa County in CDC PLACES
# Then pick the best ones for: elderly, poverty, and heat vulnerability
params = {
    "StateAbbr": "AZ",
    "Year": "2022",
    "countyfips": "04013",  # Maricopa County
}
print("Fetching CDC PLACES measures for Maricopa County...")
r = requests.get("https://chronicdata.cdc.gov/resource/cwsq-ngmh.json", params=params, timeout=60)
print(f"Status: {r.status_code}, Records: {len(r.json())}")

data = r.json()
# Get unique measures
measures = {}
for row in data:
    mid = row.get("measureid")
    m = row.get("measure")
    cat = row.get("category")
    if mid not in measures:
        measures[mid] = {"measure": m, "category": cat}

print(f"\nUnique measures available ({len(measures)}):")
for mid, info in sorted(measures.items()):
    print(f"  {mid}: {info['category']} -- {info['measure'][:70]}")