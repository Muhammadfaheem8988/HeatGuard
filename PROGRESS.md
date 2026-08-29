# PROGRESS.md - HeatGuard Alerts (FortyGuard Hackathon 26)
> Anyone picking this up mid-build: read this file first. It is the single source of truth.

---

## Current Status

**Phase:** Hour 2-5 COMPLETE. Awaiting user sign-off before Hour 5-9.
**Last updated:** 2026-08-29 19:30 PKT
**Who updated:** Antigravity (Gemini 2.5 Pro)
**Blocked on:** User validation before proceeding to next milestone.

---

## Project Summary

HeatGuard Alerts fuses hyperlocal FortyGuard temperature data with CDC PLACES vulnerability data
(census tract level) to produce a ranked top-10 risk list for Phoenix, AZ. A Streamlit dashboard
shows a choropleth map, ranked tract list, and Gemini-generated plain-language SMS alerts.
Track 04: Government and Public Policy.

---

## Milestones

| Window | Task | Status |
|--------|------|--------|
| Hr 0-2 | Confirm working API combo, lock config | DONE |
| Hr 2-5 | Pull CDC PLACES vulnerability data + TIGER geometries | DONE |
| Hr 5-9 | Spatial join, env_params pull, heat scoring | AWAITING SIGN-OFF |
| Hr 9-14 | Build Streamlit dashboard | Pending |
| Hr 14-16 | Add real request/response examples to README | Pending |
| Hr 16-18 | Deploy to Streamlit Cloud | Pending |
| Hr 18-20 | Record demo video | Pending |
| Hr 20-22 | Complete submission form | Pending |

---

## Completed Steps (most recent first)

### Hour 2-5: Vulnerability Data Pull (2026-08-29)

**CDC PLACES (dataset cwsq-ngmh) - Maricopa County, AZ - Year 2022**
- Fetched 39,719 records across 40 measures for 993 census tracts
- Key measures confirmed available and at near-100% tract coverage:
  - TEETHLOST (elderly proxy): 99.9% coverage
  - ACCESS2 (poverty/uninsurance proxy): 100% coverage
  - SHUTUTILITY (no-AC proxy, utility shut-off threat): 100% coverage
- Pivoted long->wide format, min-max normalized each factor
- Computed vulnerability_index per tract (weighted: 0.4 age + 0.3 poverty + 0.3 no_ac)
- Top vulnerable tract: 04013981000 (vuln_idx = 0.954)
- Saved to: data/cdc_places_maricopa_all.json (39,719 records)
- Saved to: data/vulnerability_scored.json (993 scored tracts)

**TIGER/Line Tract Geometries - Maricopa County**
- Fetched 1,009 tract polygons from TIGERweb REST API (no key needed)
- Format: GeoJSON FeatureCollection, WGS84, GEOID in properties
- Saved to: data/maricopa_tracts.geojson

**Scripts written:**
- api_test/fetch_all_cdc.py - Paginated CDC PLACES pull (39K records)
- api_test/build_vulnerability_dataset.py - Pivot + normalize + score
- api_test/fetch_tract_geometries.py - TIGERweb geometry pull

---

### Hour 0-2: API Validation (2026-08-29)

**CONFIRMED WORKING COMBO - Phoenix, AZ - 2024-07-15**
- POST /v1/heatmap returned activity_id: 1a368278-6c38-41d5-a60f-c5ef3396e112
- Status: Completed in under 10 seconds
- Tile data: average_temperature ~35.6 C, min ~28.4 C, max ~40.1 C
- Config locked. Cached to: cache/heatmap_Phoenix_AZ_2024-07-15_result.json

**CONFIRMED API FACTS (do not re-guess):**
- Base URL: https://api.fortyguard.com
- Auth: api-key: YOUR_KEY (request header, NOT Authorization: Bearer)
- date_time = OBJECT: {"start_date": "2024-07-15", "filter_type": 3}
  NOT separate top-level start_date + start_time fields (those return 422)
- filter_type 3 = Single Day, covers 00:00-23:59, only start_date required
- Heatmap tile fields: average_temperature, min_temperature, max_temperature
- Status endpoint: GET /v1/status/{activity_id}
- Status response shape: {"message": "Completed", "data": {"status": "Completed", "result": {"map_data": GeoJSON}}}
- env_params required fields: latitude, longitude, temperature (C), date_time object
- Heat index field name: heat_index_celsius (confirmed from docs)

---

## Next Steps (Hour 5-9) - NOT starting until user approves

1. Spatial join: match each heatmap tile (centroid) to a census tract (point-in-polygon)
2. Merge heatmap avg_temperature onto vulnerability_scored.json by tract GEOID
3. For top-20 most vulnerable tracts: call /v1/env_params to get heat_index_celsius
4. Compute final risk_score = 0.5 * norm_heat + 0.5 * norm_vulnerability
5. Rank and save top-10 to data/top10_tracts.json

---

## Key Decisions and Rationale

| Decision | Rationale |
|----------|-----------|
| Streamlit | Fastest deployable path. PRD explicit recommendation. |
| Phoenix AZ 2024-07-15 LOCKED | Confirmed non-empty tiles. Current dates have empty-tile bug. |
| filter_type=3 Single Day | Daily avg temp per tile, 100% date coverage, only start_date needed. |
| granularity=100m | Fewer tiles = lower credit cost. Sufficient for tract-level join. |
| CDC PLACES over Census ACS | No API key needed. 40 measures at 100% tract coverage. Faster. |
| TEETHLOST as elderly proxy | Only available direct signal for 65+ population in CDC PLACES. |
| ACCESS2 as poverty proxy | Lack of health insurance is strongly correlated with poverty. |
| SHUTUTILITY as no-AC proxy | Utility shut-off threat = cannot pay electricity = cannot run AC. Best available. |
| Cache-first | All API responses saved to cache/ or data/. Never re-request same combo. |

---

## Known Issues

| Issue | Status | Notes |
|-------|--------|-------|
| env_params not yet live-tested | Pending Hr 5-9 | Field names confirmed from docs; live call deferred. |
| Heatmap tile-to-tract join | Pending Hr 5-9 | Will use centroid point-in-polygon via shapely or manual bbox. |
| TEETHLOST is rate among 65+, not pct of pop | Accepted | Used as ordinal ranking signal, not absolute pct. Normalized anyway. |

---

## File Map

```
HeatGuard/
  .env                         -- API keys (never commit)
  .env.example                 -- Template
  config.py                    -- ALL constants, weights, helpers (source of truth)
  requirements.txt             -- Dependencies
  PROGRESS.md                  -- This file
  README.md                    -- Public-facing summary

  api_test/
    test_heatmap.py            -- Original heatmap validation script
    test_env_params.py         -- Original env_params validation script
    probe_fields.py            -- Field name discovery script
    fetch_all_cdc.py           -- CDC PLACES paginated pull (Hr 2-5)
    build_vulnerability_dataset.py -- Pivot + normalize + score (Hr 2-5)
    fetch_tract_geometries.py  -- TIGERweb polygon pull (Hr 2-5)

  data/
    cdc_places_maricopa_all.json    -- 39,719 CDC PLACES records (raw)
    vulnerability_scored.json       -- 993 tracts, scored + normalized
    maricopa_tracts.geojson         -- 1,009 tract polygons (TIGER)

  cache/
    heatmap_Phoenix_AZ_2024-07-15_result.json  -- Confirmed working heatmap result

  app/
    app.py                     -- Streamlit dashboard (stub, to build in Hr 9-14)
```

---

## API Notes (confirmed facts - do not re-guess)

### /v1/heatmap
- POST https://api.fortyguard.com/v1/heatmap
- Header: api-key: YOUR_KEY
- Body: polygon_aoi (GeoJSON), date_time {start_date, filter_type}, granularity, analytic_type
- Async: POST -> activity_id -> GET /v1/status/{activity_id}
- Result: data.result.map_data (GeoJSON FeatureCollection)
- Tile properties: tile_id, average_temperature, min_temperature, max_temperature
- CONFIRMED WORKING: Phoenix AZ 2024-07-15 filter_type=3 granularity=100 analytic_type=tcm

### /v1/env_params (docs-confirmed, not live-tested)
- POST https://api.fortyguard.com/v1/env_params
- Required body: latitude, longitude, temperature (C float), date_time object
- Optional: analysis list e.g. ["heat_index_celsius", "apparent_temperature_celsius"]
- Heat index field name: heat_index_celsius

### CDC PLACES
- URL: https://chronicdata.cdc.gov/resource/cwsq-ngmh.json
- No auth. Filter: StateAbbr=AZ&countyfips=04013&Year=2022
- Pagination: &%24limit=5000&%24offset=N
- 40 measures available, 993 tracts in Maricopa

### TIGERweb
- URL: https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/0/query
- No auth. Params: where="STATE='04' AND COUNTY='013'", outSR=4326, f=geojson

### Gemini API
- Model: gemini-2.0-flash
- Endpoint: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
- Header: x-goog-api-key: YOUR_KEY

---

## Environment Setup

- Python 3.10+
- pip install -r requirements.txt
- .env: FORTYGUARD_API_KEY + GEMINI_API_KEY
- Run: streamlit run app/app.py
- Repo: https://github.com/Muhammadfaheen8988/HeatGuard