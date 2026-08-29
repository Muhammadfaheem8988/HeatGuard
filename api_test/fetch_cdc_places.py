import requests, json
from pathlib import Path

# CDC PLACES has many more measures - fetch with explicit limit and offset
# Also filter to Maricopa county directly

all_data = []
offset = 0
PAGE_SIZE = 1000
print("Fetching ALL CDC PLACES records for Maricopa County (paged)...")

while True:
    params = {
        "StateAbbr": "AZ",
        "countyfips": "04013",
        "Year": "2022",
        "": str(PAGE_SIZE),
        "": str(offset),
    }
    r = requests.get("https://chronicdata.cdc.gov/resource/cwsq-ngmh.json", params=params, timeout=60)
    batch = r.json()
    print(f"  offset={offset}: got {len(batch)} records")
    if not batch:
        break
    all_data.extend(batch)
    if len(batch) < PAGE_SIZE:
        break
    offset += PAGE_SIZE

print(f"\nTotal records: {len(all_data)}")

# Get unique measures
measures = {}
for row in all_data:
    mid = row.get("measureid")
    m = row.get("measure")
    cat = row.get("category")
    if mid not in measures:
        measures[mid] = {"measure": m, "category": cat}

print(f"Unique measures ({len(measures)}):")
for mid, info in sorted(measures.items()):
    print(f"  {mid}: [{info['category']}] {info['measure'][:80]}")

# Save all data to cache for analysis
Path("data").mkdir(exist_ok=True)
with open("data/cdc_places_maricopa_2022.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f)
print(f"\nSaved {len(all_data)} records to data/cdc_places_maricopa_2022.json")