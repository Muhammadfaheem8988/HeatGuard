"""
api_test/fetch_tract_geometries.py
====================================
Fetches Maricopa County census tract geometries from Census TIGERweb REST API.
No API key needed. Returns GeoJSON polygons for each tract.
"""

import requests, json, time
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# TIGERweb ArcGIS REST API - census tracts for Arizona (state FIPS 04), Maricopa (county 013)
# Docs: https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/
TIGER_BASE = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/0/query"

def fetch_tiger_tracts(state_fips="04", county_fips="013"):
    """Fetch all census tract polygons for a county from TIGERweb."""
    all_features = []
    result_offset = 0
    page_size = 1000
    
    print(f"Fetching TIGER tract geometries for state={state_fips}, county={county_fips}...")
    
    while True:
        params = {
            "where": f"STATE='{state_fips}' AND COUNTY='{county_fips}'",
            "outFields": "GEOID,NAME,STATE,COUNTY,TRACT",
            "returnGeometry": "true",
            "outSR": "4326",  # WGS84
            "f": "geojson",
            "resultOffset": result_offset,
            "resultRecordCount": page_size,
        }
        
        r = requests.get(TIGER_BASE, params=params, timeout=120)
        print(f"  offset={result_offset}: Status {r.status_code}, bytes={len(r.content)}")
        
        if not r.ok:
            print(f"  ERROR: {r.text[:300]}")
            break
        
        data = r.json()
        features = data.get("features", [])
        print(f"  Got {len(features)} features")
        
        if not features:
            break
        
        all_features.extend(features)
        
        if len(features) < page_size:
            break
        
        result_offset += page_size
        time.sleep(0.5)
    
    print(f"Total tract features: {len(all_features)}")
    return {
        "type": "FeatureCollection",
        "features": all_features
    }


# Run the fetch
geojson = fetch_tiger_tracts("04", "013")

if geojson["features"]:
    print(f"\nSample feature:")
    f = geojson["features"][0]
    print(f"  Properties: {f.get('properties', {})}")
    print(f"  Geometry type: {f.get('geometry', {}).get('type', 'N/A')}")
    print(f"  Coordinates sample: {str(f.get('geometry', {}).get('coordinates', []))[:100]}")
    
    # Save
    out_path = DATA_DIR / "maricopa_tracts.geojson"
    with open(out_path, "w", encoding="utf-8") as f_out:
        json.dump(geojson, f_out)
    print(f"\nSaved {len(geojson['features'])} tract polygons to data/maricopa_tracts.geojson")
else:
    print("ERROR: No features returned from TIGERweb")