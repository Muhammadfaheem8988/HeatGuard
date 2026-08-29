import requests, json
from pathlib import Path

DATA_DIR = Path("data")

# The current county pull only got 5 measures. 
# Let's check if more measures exist by fetching without county filter 
# and filtering in Python, OR use measure-level queries.

# Strategy: fetch specific measureids we need for Maricopa
target_measures = ["INSURANCE", "POVERTY", "LPA", "OBESITY", "CASTHMA", "BPHIGH", "DIABETES"]

for mid in target_measures:
    url = f"https://chronicdata.cdc.gov/resource/cwsq-ngmh.json?StateAbbr=AZ&countyfips=04013&Year=2022&MeasureId={mid}&%24limit=10"
    r = requests.get(url, timeout=30)
    d = r.json()
    if isinstance(d, list) and d:
        print(f"{mid}: {len(d)} records -- measure={d[0].get('measure', 'N/A')[:50]}, sample_val={d[0].get('data_value')}")
    else:
        print(f"{mid}: 0 records (not available for this county/year)")