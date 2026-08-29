import requests, json, time
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

all_records = []
limit = 5000
offset = 0

print("Fetching ALL cwsq-ngmh records for Maricopa (no measure filter)...")
while True:
    url = f"https://chronicdata.cdc.gov/resource/cwsq-ngmh.json?StateAbbr=AZ&countyfips=04013&%24limit={limit}&%24offset={offset}"
    r = requests.get(url, timeout=120)
    d = r.json()
    if not isinstance(d, list) or not d:
        break
    all_records.extend(d)
    print(f"  offset={offset}: +{len(d)} records (total={len(all_records)})")
    if len(d) < limit:
        break
    offset += limit
    time.sleep(0.3)

print(f"Grand total: {len(all_records)} records")

# Get all unique measures
measures = {}
for row in all_records:
    mid = row.get("measureid","")
    if mid and mid not in measures:
        measures[mid] = row.get("measure","")

print(f"\nAll measures ({len(measures)}):")
for mid, name in sorted(measures.items()):
    print(f"  {mid}: {name[:80]}")

# Save all data
with open(DATA_DIR / "cdc_places_maricopa_all.json", "w") as f:
    json.dump(all_records, f)
print(f"\nSaved {len(all_records)} records")