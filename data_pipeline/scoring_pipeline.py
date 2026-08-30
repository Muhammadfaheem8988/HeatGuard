import json, time, os, requests
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("data")
CACHE_DIR = Path("cache")
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

API_KEY = "YOUR_FORTYGUARD_API_KEY"
BASE_URL = "https://api.fortyguard.com"
HEADERS = {"api-key": API_KEY, "Content-Type": "application/json"}

# ─── STEP 0: Load data ───────────────────────────────────────────────────────
print("=" * 60)
print("Loading data...")
with open("cache/heatmap_Phoenix_AZ_2024-07-15_result.json") as f:
    hm = json.load(f)
tiles = hm["data"]["result"]["map_data"]["features"]
print("  Heatmap tiles:", len(tiles))

with open("data/vulnerability_scored.json") as f:
    vuln_list = json.load(f)
vuln_by_geoid = {v["tract_geoid"]: v for v in vuln_list}
print("  Vulnerability tracts:", len(vuln_by_geoid))

with open("data/maricopa_tracts.geojson") as f:
    tracts_geojson = json.load(f)
tract_features = tracts_geojson["features"]
print("  TIGER tracts:", len(tract_features))

# ─── STEP 1: Tile centroids ───────────────────────────────────────────────────
def polygon_centroid(ring):
    lons = [c[0] for c in ring]
    lats = [c[1] for c in ring]
    return sum(lons)/len(lons), sum(lats)/len(lats)

print("\nComputing tile centroids...")
tile_centroids = []
for tile in tiles:
    props = tile["properties"]
    ring = tile["geometry"]["coordinates"][0]
    cx, cy = polygon_centroid(ring)
    tile_centroids.append({"lon": cx, "lat": cy,
        "avg_temp": props["average_temperature"],
        "min_temp": props["min_temperature"],
        "max_temp": props["max_temperature"]})
print("  Done:", len(tile_centroids))

# ─── STEP 2: Tract spatial index ─────────────────────────────────────────────
def bbox(ring):
    lons = [c[0] for c in ring]
    lats = [c[1] for c in ring]
    return min(lons), min(lats), max(lons), max(lats)

def point_in_polygon(px, py, ring):
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > py) != (yj > py)) and (px < (xj-xi)*(py-yi)/(yj-yi+1e-12)+xi):
            inside = not inside
        j = i
    return inside

print("\nBuilding tract spatial index...")
tract_spatial = []
for feat in tract_features:
    geoid = feat["properties"]["GEOID"]
    geom = feat["geometry"]
    if geom["type"] == "Polygon":
        rings = [geom["coordinates"][0]]
    elif geom["type"] == "MultiPolygon":
        rings = [poly[0] for poly in geom["coordinates"]]
    else:
        continue
    for ring in rings:
        bb = bbox(ring)
        tract_spatial.append({"geoid": geoid, "bbox": bb, "ring": ring})
print("  Spatial entries:", len(tract_spatial))

# ─── STEP 3: Spatial join ─────────────────────────────────────────────────────
print("\nRunning spatial join (this takes ~60s)...")
tract_temps = defaultdict(list)
unmatched = 0
total = len(tile_centroids)

for idx, tile in enumerate(tile_centroids):
    if idx % 8000 == 0:
        print("  Progress: {}/{}".format(idx, total))
    px, py = tile["lon"], tile["lat"]
    matched = False
    for entry in tract_spatial:
        minx, miny, maxx, maxy = entry["bbox"]
        if minx <= px <= maxx and miny <= py <= maxy:
            if point_in_polygon(px, py, entry["ring"]):
                tract_temps[entry["geoid"]].append(tile["avg_temp"])
                matched = True
                break
    if not matched:
        unmatched += 1

print("  Matched:", total - unmatched, "Unmatched:", unmatched)
print("  Tracts with heat:", len(tract_temps))

# ─── STEP 4: Aggregate + merge ────────────────────────────────────────────────
print("\nAggregating and merging...")
tract_heat = {}
for geoid, temps in tract_temps.items():
    tract_heat[geoid] = {"tract_geoid": geoid,
        "mean_temp_c": round(sum(temps)/len(temps), 4),
        "tile_count": len(temps)}

with open(DATA_DIR / "tract_heat_scores.json", "w") as f:
    json.dump(list(tract_heat.values()), f, indent=2)
print("  Saved: data/tract_heat_scores.json")

merged = []
for geoid, heat in tract_heat.items():
    vuln = vuln_by_geoid.get(geoid)
    if not vuln:
        continue
    merged.append({**heat, **vuln})
print("  Merged records:", len(merged))

temps_all = [r["mean_temp_c"] for r in merged]
t_min, t_max = min(temps_all), max(temps_all)
vuln_all = [r["vulnerability_index"] for r in merged if r.get("vulnerability_index") is not None]
v_min, v_max = min(vuln_all), max(vuln_all)

for r in merged:
    t = r["mean_temp_c"]
    v = r.get("vulnerability_index")
    r["norm_heat"] = round((t - t_min)/(t_max - t_min), 4) if t_max > t_min else 0.5
    r["norm_vuln"] = round((v - v_min)/(v_max - v_min), 4) if v is not None and v_max > v_min else 0.0
    r["risk_score_v1"] = round(0.5 * r["norm_heat"] + 0.5 * r["norm_vuln"], 4)

merged.sort(key=lambda x: x["risk_score_v1"], reverse=True)
print("\nPreliminary top-10:")
for r in merged[:10]:
    print("  {}: risk={:.3f} heat={:.2f}C vuln={:.3f}".format(
        r["tract_geoid"], r["risk_score_v1"], r["mean_temp_c"], r.get("vulnerability_index", 0)))

# ─── STEP 5: env_params for top-20 ───────────────────────────────────────────
print("\n" + "=" * 60)
print("Calling /v1/env_params for top-20 tracts...")

def call_env_params(lat, lon, temp_c, geoid):
    cache_file = CACHE_DIR / "env_params_{}.json".format(geoid)
    if cache_file.exists():
        with open(cache_file) as f:
            cached = json.load(f)
        print("  [CACHE] {}: hi={}".format(geoid, cached.get("heat_index_celsius")))
        return cached
    payload = {
        "latitude": round(float(lat), 6),
        "longitude": round(float(lon), 6),
        "temperature": round(float(temp_c), 2),
        "date_time": {"start_date": "2024-07-15", "filter_type": 3},
        "analysis": ["heat_index_celsius", "apparent_temperature_celsius", "relative_humidity_percent"]
    }
    r = requests.post("{}/v1/env_params".format(BASE_URL), headers=HEADERS, json=payload, timeout=30)
    if not r.ok:
        print("  [ERROR]", geoid, r.status_code, r.text[:150])
        return None
    resp = r.json()
    activity_id = resp.get("data", {}).get("activity_id")
    if not activity_id:
        print("  [NO activity_id]", geoid, resp)
        return None
    print("  [SUBMITTED] {} -> {}".format(geoid, activity_id))
    for attempt in range(60):
        time.sleep(5)
        sr = requests.get("{}/v1/status/{}".format(BASE_URL, activity_id),
            headers={"api-key": API_KEY}, timeout=30)
        sd = sr.json()
        status = sd.get("data", {}).get("status", "")
        if status == "Completed":
            result = sd.get("data", {}).get("result", {})
            extracted = {}
            for key in ["heat_index_celsius", "apparent_temperature_celsius", "relative_humidity_percent"]:
                val = result.get(key) or result.get("parameters", {}).get(key)
                if isinstance(val, list):
                    val = val[0] if val else None
                extracted[key] = val
            extracted["_raw"] = result
            print("  [DONE] {} hi={}".format(geoid, extracted.get("heat_index_celsius")))
            with open(cache_file, "w") as cf:
                json.dump(extracted, cf, indent=2)
            return extracted
        elif status in ("Failed", "Error"):
            print("  [FAILED]", geoid)
            return None
        if attempt % 6 == 0:
            print("  [WAIT] {} attempt={} status={}".format(geoid, attempt, status))
    print("  [TIMEOUT]", geoid)
    return None

env_results = {}
for row in merged[:20]:
    geoid = row["tract_geoid"]
    lat = row.get("centroid_lat")
    lon = row.get("centroid_lon")
    if lat is None or lon is None:
        continue
    result = call_env_params(lat, lon, row.get("mean_temp_c", 35.0), geoid)
    if result:
        env_results[geoid] = result
    time.sleep(1)

print("\nenv_params: got results for {}/20 tracts".format(len(env_results)))

# ─── STEP 6: Finalize scores ──────────────────────────────────────────────────
hi_vals = []
for ep in env_results.values():
    hi = ep.get("heat_index_celsius")
    if hi is not None:
        try: hi_vals.append(float(hi))
        except: pass
hi_min = min(hi_vals) if hi_vals else 0
hi_max = max(hi_vals) if hi_vals else 1

for row in merged:
    geoid = row["tract_geoid"]
    ep = env_results.get(geoid)
    if ep:
        hi = ep.get("heat_index_celsius")
        rh = ep.get("relative_humidity_percent")
        try: row["heat_index_c"] = float(hi) if hi is not None else None
        except: row["heat_index_c"] = None
        try: row["relative_humidity"] = float(rh) if rh is not None else None
        except: row["relative_humidity"] = None
        if row["heat_index_c"] is not None and hi_max > hi_min:
            norm_hi = (row["heat_index_c"] - hi_min) / (hi_max - hi_min)
            row["norm_heat_refined"] = round(0.4*row["norm_heat"] + 0.6*norm_hi, 4)
        else:
            row["norm_heat_refined"] = row["norm_heat"]
    else:
        row["heat_index_c"] = None
        row["relative_humidity"] = None
        row["norm_heat_refined"] = row["norm_heat"]
    row["risk_score_final"] = round(0.5*row["norm_heat_refined"] + 0.5*row["norm_vuln"], 4)

merged.sort(key=lambda x: x["risk_score_final"], reverse=True)

print("\nFINAL TOP-10:")
print("-" * 70)
for i, r in enumerate(merged[:10]):
    hi_str = "{:.1f}C".format(r["heat_index_c"]) if r.get("heat_index_c") else "N/A"
    print("  #{} {} risk={:.3f} heat={:.1f}C HI={} vuln={:.3f}".format(
        i+1, r["tract_geoid"], r["risk_score_final"],
        r["mean_temp_c"], hi_str, r.get("vulnerability_index", 0)))

# ─── STEP 7: Save outputs ────────────────────────────────────────────────────
KEEP = ["tract_geoid","centroid_lat","centroid_lon","total_population",
        "mean_temp_c","heat_index_c","relative_humidity",
        "vulnerability_index","norm_heat","norm_vuln","risk_score_final",
        "pct_age_65_proxy","pct_poverty_proxy","pct_no_ac_proxy",
        "norm_age_65","norm_poverty","norm_no_ac","tile_count"]

top10 = [{k: r.get(k) for k in KEEP} for r in merged[:10]]
with open(DATA_DIR / "top10_tracts.json", "w") as f:
    json.dump(top10, f, indent=2)
print("\nSaved: data/top10_tracts.json")

with open(DATA_DIR / "merged_all_tracts.json", "w") as f:
    json.dump(merged, f, indent=2)
print("Saved: data/merged_all_tracts.json")

print("\n" + "=" * 60)
print("Hour 5-9 COMPLETE.")