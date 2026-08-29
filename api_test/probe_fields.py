import requests, json, time

API_KEY = "f45468840a11216c24f4e7e24ab226f5"
BASE = "https://api.fortyguard.com"
HEADERS = {"api-key": API_KEY, "Content-Type": "application/json"}

AOI = {"type":"FeatureCollection","features":[{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-112.15,33.37],[-111.85,33.37],[-111.85,33.63],[-112.15,33.63],[-112.15,33.37]]]}}]}

date_formats = ["2024-07-15T00:00:00","2024-07-15 00:00:00","2024-07-15","2024-07-15T12:00:00"]

print("=== Probing date_time field ===")
for dt in date_formats:
    payload = {"polygon_aoi": AOI, "filter_type": 3, "granularity": 100, "analytic_type": "tcm", "date_time": dt}
    print(f"\ndate_time={dt}")
    r = requests.post(f"{BASE}/v1/heatmap", headers=HEADERS, json=payload, timeout=30)
    print(f"  Status: {r.status_code}")
    resp = r.json()
    if r.status_code not in (422, 400):
        print("  SUCCESS:", json.dumps(resp, indent=2)[:3000])
        break
    else:
        print("  Error:", str(resp.get("message", resp.get("detail","")))[:300])

print("\n=== Probe OpenAPI schema ===")
for path in ["/openapi.json", "/v1/openapi.json", "/docs/openapi.json", "/api-json"]:
    r = requests.get(f"{BASE}{path}", headers=HEADERS, timeout=10)
    print(f"GET {path}: {r.status_code} {r.text[:300]}")
