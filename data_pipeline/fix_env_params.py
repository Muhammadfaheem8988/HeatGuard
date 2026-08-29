import json
from pathlib import Path

DATA_DIR = Path("data")
CACHE_DIR = Path("cache")

# Re-extract heat index from cached env_params responses (correct path)
def extract_hi(cache_path):
    with open(cache_path) as f:
        d = json.load(f)
    raw = d.get("_raw", {})
    locations = raw.get("locations", [])
    if not locations:
        return None, None, None
    params = locations[0].get("parameters", {})
    hi_list = params.get("heat_index_celsius", [])
    rh_list = params.get("relative_humidity_percent", [])
    at_list = params.get("apparent_temperature_celsius", [])
    hi_max = max(hi_list) if hi_list else None
    hi_mean = sum(hi_list)/len(hi_list) if hi_list else None
    rh_mean = sum(rh_list)/len(rh_list) if rh_list else None
    return hi_max, hi_mean, rh_mean

# Load all cached env_params
env_results = {}
for cf in CACHE_DIR.glob("env_params_*.json"):
    geoid = cf.stem.replace("env_params_", "")
    hi_max, hi_mean, rh_mean = extract_hi(cf)
    env_results[geoid] = {"hi_max": hi_max, "hi_mean": hi_mean, "rh_mean": rh_mean}
    print("  {}: hi_max={:.1f} hi_mean={:.1f} rh={:.1f}%".format(
        geoid,
        hi_max if hi_max else 0,
        hi_mean if hi_mean else 0,
        rh_mean if rh_mean else 0))

print("\nGot env_params for {} tracts".format(len(env_results)))

# Reload merged
with open(DATA_DIR / "merged_all_tracts.json") as f:
    merged = json.load(f)

# Apply heat index to merged records
hi_vals = [v["hi_max"] for v in env_results.values() if v["hi_max"] is not None]
hi_min = min(hi_vals) if hi_vals else 0
hi_max_global = max(hi_vals) if hi_vals else 1

# Also need norm_heat range
temps_all = [r["mean_temp_c"] for r in merged]
t_min, t_max = min(temps_all), max(temps_all)
vuln_all = [r["vulnerability_index"] for r in merged if r.get("vulnerability_index") is not None]
v_min, v_max = min(vuln_all), max(vuln_all)

for r in merged:
    geoid = r["tract_geoid"]
    ep = env_results.get(geoid)
    r["norm_heat"] = round((r["mean_temp_c"] - t_min)/(t_max - t_min), 4) if t_max > t_min else 0.5
    r["norm_vuln"] = round((r["vulnerability_index"] - v_min)/(v_max - v_min), 4) if r.get("vulnerability_index") is not None and v_max > v_min else 0.0
    if ep and ep["hi_max"] is not None:
        r["heat_index_c"] = round(ep["hi_max"], 2)
        r["heat_index_mean_c"] = round(ep["hi_mean"], 2) if ep["hi_mean"] else None
        r["relative_humidity"] = round(ep["rh_mean"], 1) if ep["rh_mean"] else None
        norm_hi = (ep["hi_max"] - hi_min) / (hi_max_global - hi_min) if hi_max_global > hi_min else 0.5
        r["norm_heat_refined"] = round(0.4*r["norm_heat"] + 0.6*norm_hi, 4)
    else:
        r["heat_index_c"] = None
        r["heat_index_mean_c"] = None
        r["relative_humidity"] = None
        r["norm_heat_refined"] = r["norm_heat"]
    r["risk_score_final"] = round(0.5*r["norm_heat_refined"] + 0.5*r["norm_vuln"], 4)

merged.sort(key=lambda x: x["risk_score_final"], reverse=True)

print("\nFINAL TOP-10 (with corrected heat index):")
print("-" * 80)
for i, r in enumerate(merged[:10]):
    hi_str = "{:.1f}C".format(r["heat_index_c"]) if r.get("heat_index_c") else "N/A"
    print("  #{} {} risk={:.3f} heat={:.1f}C HI_max={} vuln={:.3f}".format(
        i+1, r["tract_geoid"], r["risk_score_final"],
        r["mean_temp_c"], hi_str, r.get("vulnerability_index", 0)))

# Save updated top10
KEEP = ["tract_geoid","centroid_lat","centroid_lon","total_population",
        "mean_temp_c","heat_index_c","heat_index_mean_c","relative_humidity",
        "vulnerability_index","norm_heat","norm_vuln","risk_score_final",
        "pct_age_65_proxy","pct_poverty_proxy","pct_no_ac_proxy",
        "norm_age_65","norm_poverty","norm_no_ac","tile_count"]
top10 = [{k: r.get(k) for k in KEEP} for r in merged[:10]]
with open(DATA_DIR / "top10_tracts.json", "w") as f:
    json.dump(top10, f, indent=2)
print("\nSaved: data/top10_tracts.json (corrected)")

with open(DATA_DIR / "merged_all_tracts.json", "w") as f:
    json.dump(merged, f, indent=2)
print("Saved: data/merged_all_tracts.json (corrected)")