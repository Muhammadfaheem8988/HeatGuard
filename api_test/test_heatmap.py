"""
api_test/test_heatmap.py
========================
Hour 0-2: Confirm a working city/date/AOI combo for /v1/heatmap.
Tests multiple date candidates and reports which returns non-empty tiles.

USAGE:
    python api_test/test_heatmap.py

OUTPUT:
    - Prints working combos (n_cells > 0) and failed combos
    - On success, prints the exact config values to paste into config.py
    - Saves the full response to cache/heatmap_<date>.json for downstream use
"""

import sys
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    FORTYGUARD_API_KEY,
    FG_BASE_URL,
    DEMO_AOI_PHOENIX,
    DEMO_AOI_HOUSTON,
    GRANULARITY,
    FILTER_TYPE,
    ANALYTIC_TYPE,
    POLL_INTERVAL_SECONDS,
    POLL_MAX_RETRIES,
    CACHE_DIR,
)

# ---------------------------------------------
# Test matrix: city ? (date, AOI) combos to try
# ---------------------------------------------
TEST_COMBOS = [
    {
        "city": "Phoenix, AZ",
        "date": "2024-07-15",
        "start_time": "00:00",
        "aoi": DEMO_AOI_PHOENIX,
        "notes": "Phoenix Jul 2024 heat event — primary candidate"
    },
    {
        "city": "Phoenix, AZ",
        "date": "2024-08-01",
        "start_time": "00:00",
        "aoi": DEMO_AOI_PHOENIX,
        "notes": "Phoenix Aug 2024 backup"
    },
    {
        "city": "Phoenix, AZ",
        "date": "2023-07-18",
        "start_time": "00:00",
        "aoi": DEMO_AOI_PHOENIX,
        "notes": "Phoenix Jul 2023 heat event backup"
    },
    {
        "city": "Houston, TX",
        "date": "2024-07-08",
        "start_time": "00:00",
        "aoi": DEMO_AOI_HOUSTON,
        "notes": "Houston Jul 2024 backup city"
    },
]


def submit_heatmap_request(combo):
    """POST to /v1/heatmap and return activity_id."""
    url = f"{FG_BASE_URL}/v1/heatmap"
    headers = {
        "api-key": FORTYGUARD_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "polygon_aoi": combo["aoi"],
        "start_date": combo["date"],
        "start_time": combo["start_time"],
        "filter_type": FILTER_TYPE,
        "granularity": GRANULARITY,
        "analytic_type": ANALYTIC_TYPE,
    }
    print(f"\n[SUBMIT] {combo['city']} | {combo['date']} | {combo['notes']}")
    print(f"  POST {url}")
    print(f"  Payload: {json.dumps({k: v for k, v in payload.items() if k != 'polygon_aoi'}, indent=2)}")
    
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
    """Poll /v1/status/{activity_id} until Completed or error. Returns final response."""
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
            # Still processing — continue polling
        except Exception as e:
            print(f"  Poll attempt {attempt+1} error: {e}")
    
    print(f"  TIMEOUT after {POLL_MAX_RETRIES} attempts")
    return None


def fetch_result(activity_id, data_url=None):
    """
    Fetch the actual result data from completed activity.
    Try data_url from status response first, otherwise derive from activity_id.
    """
    # Some APIs embed the result URL in the status response
    if data_url:
        url = data_url
    else:
        url = f"{FG_BASE_URL}/v1/result/{activity_id}"
    
    headers = {"api-key": FORTYGUARD_API_KEY}
    print(f"\n[FETCH RESULT] {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ERROR fetching result: {e}")
        # If response body has useful info, print it
        try:
            print(f"  Response body: {resp.text[:500]}")
        except:
            pass
        return None


def check_tile_count(result_data):
    """Check if result has non-empty tiles. Returns (n_cells, has_data)."""
    if not result_data:
        return 0, False
    
    # Try common response shapes
    n_cells = result_data.get("n_cells", None)
    features = result_data.get("features", [])
    
    if n_cells is not None:
        return n_cells, n_cells > 0
    elif features:
        return len(features), len(features) > 0
    else:
        # Dig one level deeper
        data = result_data.get("data", {})
        if isinstance(data, dict):
            n_cells = data.get("n_cells", 0)
            features = data.get("features", [])
            return n_cells or len(features), (n_cells or len(features)) > 0
        return 0, False


def save_to_cache(data, filename):
    """Save JSON response to cache/ directory."""
    cache_path = Path(CACHE_DIR)
    cache_path.mkdir(exist_ok=True)
    filepath = cache_path / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved to {filepath}")
    return str(filepath)


def main():
    print("=" * 60)
    print("HeatGuard — /v1/heatmap API Validation (Hour 0-2)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"FortyGuard API key: {'SET (' + FORTYGUARD_API_KEY[:8] + '...)' if FORTYGUARD_API_KEY else 'NOT SET — check .env'}")
    print("=" * 60)
    
    if not FORTYGUARD_API_KEY:
        print("\nERROR: FORTYGUARD_API_KEY not set. Create a .env file with:")
        print("  FORTYGUARD_API_KEY=your_key_here")
        sys.exit(1)
    
    working_combos = []
    failed_combos = []
    
    # Try combos one at a time (stop after first success to save credits)
    for combo in TEST_COMBOS:
        print(f"\n{'='*60}")
        print(f"Testing: {combo['city']} | {combo['date']}")
        print(f"{'='*60}")
        
        # Step 1: Submit
        submit_resp = submit_heatmap_request(combo)
        if not submit_resp:
            failed_combos.append({**combo, "fail_reason": "Submit request failed"})
            print("  -> FAILED at submit. Moving to next combo.")
            continue
        
        # Save raw submit response
        save_to_cache(
            {"request": {k: v for k, v in combo.items() if k != "aoi"}, "submit_response": submit_resp},
            f"submit_{combo['city'].replace(', ', '_').replace(' ', '_')}_{combo['date']}.json"
        )
        
        # Extract activity_id (try common field names)
        activity_id = (
            submit_resp.get("activity_id") or
            submit_resp.get("activityId") or
            submit_resp.get("id") or
            submit_resp.get("job_id")
        )
        
        if not activity_id:
            print(f"  No activity_id found in response: {submit_resp}")
            failed_combos.append({**combo, "fail_reason": "No activity_id in submit response"})
            continue
        
        print(f"  activity_id: {activity_id}")
        
        # Step 2: Poll
        status_resp = poll_status(activity_id)
        if not status_resp:
            failed_combos.append({**combo, "fail_reason": "Poll failed or timed out", "activity_id": activity_id})
            print("  -> FAILED at poll. Moving to next combo.")
            continue
        
        # Save status response
        save_to_cache(
            {"activity_id": activity_id, "status_response": status_resp},
            f"status_{combo['city'].replace(', ', '_').replace(' ', '_')}_{combo['date']}.json"
        )
        
        # Step 3: Fetch result
        # Status response might directly contain results or a URL
        result_data = status_resp
        data_url = status_resp.get("result_url") or status_resp.get("data_url") or status_resp.get("download_url")
        
        if data_url:
            result_data = fetch_result(activity_id, data_url)
        elif "features" not in status_resp and "n_cells" not in status_resp:
            # Try fetching from a result endpoint
            result_data = fetch_result(activity_id)
        
        n_cells, has_data = check_tile_count(result_data)
        
        print(f"\n[RESULT] n_cells={n_cells} | has_data={has_data}")
        
        if has_data:
            # SUCCESS — save full result
            cache_filename = f"heatmap_{combo['city'].replace(', ', '_').replace(' ', '_')}_{combo['date']}.json"
            save_to_cache(result_data, cache_filename)
            
            working_combos.append({
                **combo,
                "n_cells": n_cells,
                "activity_id": activity_id,
                "cache_file": cache_filename
            })
            
            print(f"\n{'='*60}")
            print(f"SUCCESS! Working combo found:")
            print(f"  City:        {combo['city']}")
            print(f"  Date:        {combo['date']}")
            print(f"  Start time:  {combo['start_time']}")
            print(f"  n_cells:     {n_cells}")
            print(f"  Cached to:   cache/{cache_filename}")
            print(f"\nPaste these into config.py:")
            print(f"  DEMO_CITY = \"{combo['city']}\"")
            print(f"  DEMO_DATE = \"{combo['date']}\"")
            print(f"  DEMO_START_TIME = \"{combo['start_time']}\"")
            print(f"{'='*60}")
            
            # Stop after first success (save credits)
            print("\nStopping after first success to conserve API credits.")
            break
        else:
            failed_combos.append({
                **combo,
                "fail_reason": f"Empty tiles (n_cells={n_cells})",
                "activity_id": activity_id
            })
            print(f"  -> Empty tiles. Trying next combo...")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Working combos: {len(working_combos)}")
    for c in working_combos:
        print(f"  ? {c['city']} | {c['date']} | n_cells={c['n_cells']}")
    
    print(f"\nFailed combos: {len(failed_combos)}")
    for c in failed_combos:
        print(f"  ? {c['city']} | {c['date']} | reason={c['fail_reason']}")
    
    if not working_combos:
        print("\n[ACTION REQUIRED] All combos failed. Next steps:")
        print("  1. Check API key is correct")
        print("  2. Check FortyGuard API base URL in config.py (FG_BASE_URL)")
        print("  3. Try different historical dates (2022, 2021)")
        print("  4. Check hackathon Slack for working combos from other teams")
        sys.exit(1)
    
    return working_combos[0]


if __name__ == "__main__":
    main()
