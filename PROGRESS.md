# PROGRESS.md - HeatGuard Alerts (FortyGuard Hackathon 26)
> Anyone picking this up mid-build: read this file first. It is the single source of truth.

---

## Current Status

**Phase:** Hour 9-14 COMPLETE. Dashboard running at http://localhost:8501. Awaiting user sign-off before deployment.
**Last updated:** 2026-08-29 20:30 PKT
**Who updated:** Antigravity (Gemini 2.5 Pro)
**Blocked on:** User validation before proceeding to Streamlit Cloud deployment.

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
| Hr 5-9 | Spatial join, env_params pull, heat scoring | DONE |
| Hr 9-14 | Build Streamlit dashboard | DONE - running on localhost:8501 |
| Hr 14-16 | Add real request/response examples to README | AWAITING SIGN-OFF |
| Hr 16-18 | Deploy to Streamlit Cloud | AWAITING SIGN-OFF |
| Hr 18-20 | Record demo video | Pending |
| Hr 20-22 | Complete submission form | Pending |

---

## Completed Steps (most recent first)

### Hour 9-14: Streamlit Dashboard (2026-08-29)

**Dashboard: app/app.py**
- Full Streamlit app with dark theme, custom CSS, gradient header
- Left sidebar: scoring methodology explanation, data credits
- Top KPI strip: 5 metrics (risk score, tile temp, heat index, vulnerability, tracts analyzed)
- Choropleth map (Folium, CartoDB Dark Matter tiles):
  - All 319 tracts colored by risk intensity (dark=low, red=high)
  - Top-10 numbered pins with popup details per tract
- Top-10 ranked list (right panel): expandable cards per tract with all metrics
- Gemini Alert Generator: multiselect tracts, click Generate -> Gemini 2.0 Flash alert text
  - Static fallback alerts if Gemini key unavailable
- Full data table (expandable) with all 10 tracts
- Verified loading in browser: no errors, all elements rendering

**CONFIRMED WORKING:**
- streamlit 1.62.0, folium 0.20.0, streamlit-folium OK
- Dashboard loads in <10s, map renders, pins visible, cards expand
- All real data (FortyGuard API + CDC PLACES + TIGER)

---

### Hour 5-9: Spatial Join + Scoring (2026-08-29)

**Spatial join: 80,336 heatmap tiles -> 325 tracts (100% matched)**
- Pure Python ray-casting point-in-polygon (no shapely dependency)
- All 80K tiles matched (0 unmatched)

**env_params: called for top-20 tracts**
- 24-hour hourly heat index, apparent temp, relative humidity per tract centroid
- Extracted peak heat index (max of 24 hourly values)
- Correct response path: _raw.locations[0].parameters.heat_index_celsius (array of 24)
- Activity IDs cached in cache/env_params_*.json

**Final risk_score = 0.5 * norm_heat_refined + 0.5 * norm_vuln**
- norm_heat_refined = 0.4 * norm_raw_temp + 0.6 * norm_peak_heat_index

**FINAL TOP-10:**
| Rank | Tract | Risk | Avg Temp | HI Peak | Vulnerability |
|------|-------|------|----------|---------|---------------|
| 1 | 04013981000 | 0.855 | 36.6°C | 44.5°C | 0.954 |
| 2 | 04013106801 | 0.757 | 36.3°C | 45.4°C | 0.646 |
| 3 | 04013106001 | 0.707 | 36.5°C | 45.9°C | 0.428 |
| 4 | 04013111501 | 0.682 | 36.6°C | 45.6°C | 0.420 |
| 5 | 04013111601 | 0.664 | 36.6°C | 45.5°C | 0.410 |
| 6 | 04013111502 | 0.657 | 36.6°C | 45.6°C | 0.377 |
| 7 | 04013113502 | 0.652 | 36.6°C | 44.4°C | 0.597 |
| 8 | 04013115200 | 0.650 | 36.2°C | N/A | 0.498 |
| 9 | 04013111401 | 0.646 | 36.6°C | N/A | 0.329 |
| 10 | 04013114302 | 0.642 | 35.9°C | N/A | 0.600 |

Saved: data/top10_tracts.json, data/merged_all_tracts.json, data/tract_heat_scores.json

---

### Hour 2-5: Vulnerability Data Pull (2026-08-29)

- CDC PLACES 39,719 records, 40 measures, 993 tracts: data/cdc_places_maricopa_all.json
- Scored 993 tracts -> data/vulnerability_scored.json
- TIGER 1,009 tract polygons -> data/maricopa_tracts.geojson

---

### Hour 0-2: API Validation (2026-08-29)

- Phoenix AZ 2024-07-15 CONFIRMED WORKING
- date_time = OBJECT {"start_date":"2024-07-15","filter_type":3}
- Cached: cache/heatmap_Phoenix_AZ_2024-07-15_result.json

---

## Next Steps (Hr 14-16+) - NOT starting until user approves

1. Add README with real curl request/response examples (hackathon requirement)
2. Create .streamlit/secrets.toml for cloud deployment
3. Push to GitHub
4. Deploy to Streamlit Cloud (share.streamlit.io)
5. Record demo video
6. Complete FortyGuard submission form

---

## Key Decisions and Rationale

| Decision | Rationale |
|----------|-----------|
| Streamlit | Fastest deployable path. PRD explicit recommendation. |
| Phoenix AZ 2024-07-15 LOCKED | Confirmed non-empty tiles. Current dates have empty-tile bug. |
| filter_type=3 Single Day | Daily avg temp per tile, only start_date needed. |
| granularity=100m | Fewer tiles = lower credit cost. Sufficient for tract-level join. |
| CDC PLACES over Census ACS | No API key needed. 40 measures at 100% tract coverage. |
| TEETHLOST as elderly proxy | Only available direct signal for 65+ population in CDC PLACES. |
| ACCESS2 as poverty proxy | Lack of health insurance correlates strongly with poverty. |
| SHUTUTILITY as no-AC proxy | Utility shut-off threat = cannot pay electricity = cannot run AC. |
| env_params peak HI (max of 24h) | Peak = worst-case scenario for heat illness risk. |
| Cache-first | All API responses saved. Never re-request same combo. |
| Pure Python PIP = no shapely | Avoids heavy dependency; ray-casting sufficient at 100m tile size. |

---

## Known Issues

| Issue | Status | Notes |
|-------|--------|-------|
| CARTO API KEY watermark on map | Minor | CartoDB Dark Matter sometimes shows this; use OpenStreetMap tile as fallback |
| 8 of 10 tracts have no HI (env_params only for top-20 by v1 score) | Accepted | Sufficient for demo; top-7 all have HI |
| Gemini key needed for live alerts | Accepted | Static fallback alerts provided for all top-3 |

---

## File Map

app/
  app.py                          -- Streamlit dashboard (MAIN ENTRYPOINT)

data_pipeline/
  scoring_pipeline.py             -- Spatial join + env_params + scoring
  fix_env_params.py               -- Fixes heat index extraction from cached responses

data/
  cdc_places_maricopa_all.json    -- 39,719 CDC PLACES records (raw)
  vulnerability_scored.json       -- 993 tracts, scored + normalized
  maricopa_tracts.geojson         -- 1,009 tract polygons (TIGER)
  tract_heat_scores.json          -- Heat aggregated per tract from heatmap
  top10_tracts.json               -- FINAL: top-10 ranked tracts for dashboard
  merged_all_tracts.json          -- All 319 scored tracts (full data)

cache/
  heatmap_Phoenix_AZ_2024-07-15_result.json  -- Heatmap response (80,336 tiles)
  env_params_040130*.json                    -- env_params per top-20 tract (20 files)

---

## API Notes (confirmed - do not re-guess)

### /v1/heatmap - CONFIRMED WORKING
- POST https://api.fortyguard.com/v1/heatmap
- Header: api-key: YOUR_KEY
- date_time = OBJECT {"start_date":"2024-07-15","filter_type":3}
- Result path: data.result.map_data.features[].properties.average_temperature
- Cached: cache/heatmap_Phoenix_AZ_2024-07-15_result.json

### /v1/env_params - CONFIRMED WORKING
- POST https://api.fortyguard.com/v1/env_params
- Required: latitude, longitude, temperature (C float), date_time object
- analysis: ["heat_index_celsius","apparent_temperature_celsius","relative_humidity_percent"]
- Result path: data.result.locations[0].parameters.heat_index_celsius (array of 24 hourly values)
- Cached: cache/env_params_{geoid}.json (20 files)

### CDC PLACES
- https://chronicdata.cdc.gov/resource/cwsq-ngmh.json
- Filter: StateAbbr=AZ&countyfips=04013&Year=2022
- Pagination: %24limit=5000&%24offset=N

### Gemini API
- Model: gemini-2.0-flash
- POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
- Header: x-goog-api-key: YOUR_KEY

---

## Environment Setup

- Python 3.10+
- pip install -r requirements.txt
- .env: FORTYGUARD_API_KEY + GEMINI_API_KEY
- Run: streamlit run app/app.py
- Repo: https://github.com/Muhammadfaheen8988/HeatGuard