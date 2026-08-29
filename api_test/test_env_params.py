"""
api_test/test_env_params.py
============================
Hour 0-2: Confirm /v1/env_params response shape, exact field names,
and heat index units. This MUST run against the same city/date as
the confirmed heatmap combo.

USAGE:
    python api_test/test_env_params.py

OUTPUT:
    - Prints full response JSON so we can see exact field names
    - Saves to cache/env_params_<city>_<date>.json
    - Logs the heat_index field name for downstream use
"""

import sys
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    FORTYGUARD_API_KEY,
    FG_BASE_URL,
    DEMO_DATE,
    DEMO_DATE_CANDIDATE_1,
    DEMO_START_TIME,
    POLL_INTERVAL_SECONDS,
    POLL_MAX_RETRIES,
    CACHE_DIR,
)

# Use confirmed date if set, otherwise use candidate 1
TEST_DATE = DEMO_DATE or DEMO_DATE_CANDIDATE_1
TEST_START_TIME = DEMO_START_TIME or "12:00"  # Test at noon local time

# Test points: Phoenix city center + a few representative lat/lon
# These will be replaced with actual tract centroids after spatial join
TEST_POINTS = [
    {"lat": 33.4484, "lon": -112.0740, "label": "Phoenix City Center"},
    {"lat": 33.5722, "lon": -112.0890, "label": "North Phoenix"},
    {"lat": 33.3942, "lon": -111.9773, "label": "Tempe/East Valley"},
]


def submit_env_params_request(lat, lon, label):
    """POST to /v1/env_params for a single point."""
    url = f"{FG_BASE_URL}/v1/env_params"
    headers = {
        "api-key": FORTYGUARD_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "lat": lat,
        "lon": lon,
        "start_date": TEST_DATE,
        "start_time": TEST_START_TIME,
    }
    
    print(f"\n[SUBMIT env_params] {label} | ({lat}, {lon}) | {TEST_DATE} {TEST_START_TIME}")
    print(f"  POST {url}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(f"  Response ({resp.status_code}): {json.dumps(data, indent=2)}")
        return data
    except requests.exceptions.HTTPError as e:
        print(f"  HTTP ERROR: {e}")
        print(f"  Response body: {e.response.text if e.response else 'N/A'}")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def poll_status(activity_id):
    """Poll /v1/status/{activity_id} until Completed."""
    url = f"{FG_BASE_URL}/v1/status/{activity_id}"
    headers = {"api-key": FORTYGUARD_API_KEY}
    
    print(f"\n[POLL] activity_id={activity_id}")
    for attempt in range(POLL_MAX_RETRIES):
        time.sleep(POLL_INTERVAL_SECONDS)
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "unknown")
            print(f"  Attempt {attempt+1}: status={status}")
            
            if status.lower() in ("completed", "complete", "done", "success"):
                return data
            elif status.lower() in ("failed", "error", "cancelled"):
                print(f"  FAILED: {json.dumps(data, indent=2)}")
                return None
        except Exception as e:
            print(f"  Poll attempt {attempt+1} error: {e}")
    
    print(f"  TIMEOUT")
    return None


def analyze_env_params_response(result_data, label):
    """Print analysis of env_params response — identify field names."""
    print(f"\n[FIELD ANALYSIS] {label}")
    print(f"  Top-level keys: {list(result_data.keys()) if isinstance(result_data, dict) else type(result_data)}")
    
    # Try to find heat index field
    heat_index_candidates = [
        "heat_index", "heat_index_c", "heat_index_f", "feels_like",
        "apparent_temperature", "apparent_temp", "HeatIndex",
        "heat_index_celsius", "hi", "apparent_temp_c"
    ]
    
    def search_nested(d, candidates, depth=0, prefix=""):
        if depth > 3:
            return
        if isinstance(d, dict):
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if any(c.lower() in k.lower() for c in candidates):
                    print(f"  CANDIDATE HEAT INDEX FIELD: {full_key} = {v}")
                if isinstance(v, (dict, list)):
                    search_nested(v, candidates, depth+1, full_key)
        elif isinstance(d, list) and len(d) > 0:
            search_nested(d[0], candidates, depth+1, f"{prefix}[0]")
    
    search_nested(result_data, heat_index_candidates)
    
    # Print full structure (first item if list)
    if isinstance(result_data, list):
        print(f"\n  Full first item: {json.dumps(result_data[0] if result_data else {}, indent=4)}")
    else:
        print(f"\n  Full response: {json.dumps(result_data, indent=4)}")


def main():
    print("=" * 60)
    print("HeatGuard — /v1/env_params API Validation (Hour 0-2)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Test date: {TEST_DATE} | Start time: {TEST_START_TIME}")
    print(f"FortyGuard API key: {'SET (' + FORTYGUARD_API_KEY[:8] + '...)' if FORTYGUARD_API_KEY else 'NOT SET'}")
    print("=" * 60)
    
    if not FORTYGUARD_API_KEY:
        print("ERROR: FORTYGUARD_API_KEY not set. Check .env file.")
        sys.exit(1)
    
    results = {}
    
    # Test first point (stop after one success to save credits)
    for point in TEST_POINTS[:1]:
        submit_resp = submit_env_params_request(point["lat"], point["lon"], point["label"])
        if not submit_resp:
            print("Submit failed. Check API key and endpoint.")
            continue
        
        activity_id = (
            submit_resp.get("activity_id") or
            submit_resp.get("activityId") or
            submit_resp.get("id") or
            submit_resp.get("job_id")
        )
        
        if not activity_id:
            print(f"No activity_id in response: {submit_resp}")
            continue
        
        status_resp = poll_status(activity_id)
        if not status_resp:
            print("Poll failed.")
            continue
        
        # Fetch result (may be in status_resp or a separate URL)
        result_data = status_resp
        data_url = status_resp.get("result_url") or status_resp.get("data_url") or status_resp.get("download_url")
        
        if data_url:
            headers = {"api-key": FORTYGUARD_API_KEY}
            try:
                resp = requests.get(data_url, headers=headers, timeout=60)
                resp.raise_for_status()
                result_data = resp.json()
            except Exception as e:
                print(f"Failed to fetch from data_url: {e}")
        
        analyze_env_params_response(result_data, point["label"])
        
        # Save
        cache_path = Path(CACHE_DIR)
        cache_path.mkdir(exist_ok=True)
        cache_file = cache_path / f"env_params_{TEST_DATE}_{point['label'].replace(' ', '_').replace('/', '_')}.json"
        with open(cache_file, "w") as f:
            json.dump({
                "request": point,
                "date": TEST_DATE,
                "start_time": TEST_START_TIME,
                "result": result_data
            }, f, indent=2)
        print(f"\n[SAVED] {cache_file}")
        
        results[point["label"]] = result_data
        
        # One successful call is enough to confirm field names
        break
    
    print(f"\n{'='*60}")
    print("env_params validation complete.")
    print("=> Update API notes in PROGRESS.md with the heat_index field name found above.")
    print(f"{'='*60}")
    
    return results


if __name__ == "__main__":
    main()
