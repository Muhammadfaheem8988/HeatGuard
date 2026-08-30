# PROGRESS.md - HeatGuard Alerts (FortyGuard Hackathon 26)
> Anyone picking this up: read this file first. It is the single source of truth.

---

## Known Platform Behavior

Confirmed `/v1/heatmap` returns empty tiles (`n_cells: 0`) for recent/current dates
during the hackathon window (Aug 2026). Locked demo to `2024-07-15` after validating
full tile coverage (80,336 tiles returned). See `DEMO_DATE` constant in `app/app.py`
and `data_pipeline/scoring_pipeline.py`, and README `## Warning Disclaimer` for full rationale.


## Current Status

**Phase:** Dashboard + Gemini DONE. Stopping for night. Resume tomorrow.
**Last updated:** 2026-08-29 20:30 PKT
**Git commit:** 233911d (main branch)
**Repo:** https://github.com/Muhammadfaheen8988/HeatGuard

---

## To Resume Tomorrow - Run This First

```
cd D:\CODING\Hackathons\FortyGuard\HeatGuard
streamlit run app/app.py
```

Dashboard opens at http://localhost:8501

---

## Milestones

| Window | Task | Status |
|--------|------|--------|
| Hr 0-2 | FortyGuard API validation | DONE |
| Hr 2-5 | CDC PLACES vulnerability data + TIGER geometries | DONE |
| Hr 5-9 | Spatial join, env_params, heat scoring | DONE |
| Hr 9-14 | Streamlit dashboard | DONE |
| Hr 14-16 | README with real API proof | TODO TOMORROW |
| Hr 16-18 | Deploy to Streamlit Cloud | TODO TOMORROW |
| Hr 18-20 | Demo video | TODO TOMORROW (user records) |
| Hr 20-22 | Submission form | TODO TOMORROW (user fills) |

---

## Tomorrow Tasks (in order)

1. **README.md** - Add real curl examples with actual activity_ids + responses (hackathon requirement)
2. **Deploy** - share.streamlit.io, add secrets, get public URL
3. **Demo video** - user records, I provide script/checklist
4. **Submission form** - I prep all text to paste

---

## Completed Steps (most recent first)

### Gemini Integration Fixed (2026-08-29 20:30 PKT)
- Model: gemini-3.5-flash-lite (confirmed working with this key)
- Key: stored in .env as GEMINI_API_KEY (never hardcoded)
- Root cause of earlier failures: thinking model returns text+thoughtSignature in same part.
  The text field IS the final answer. Fixed extraction: just take p["text"] for all parts.
- maxOutputTokens: 400, timeout: 30s
- Verified output: "HEAT ALERT | SW Phoenix Tract 981000: Extreme heat index of 112.1F
  threatens this highly vulnerable, predominantly elderly population. Deploy teams
  immediately to distribute water, check on unconditioned homes..."
- app/app.py updated + pushed to GitHub

### Dashboard Built (2026-08-29 ~20:15 PKT)
- app/app.py: Streamlit, dark theme, custom CSS, gradient header
- Folium choropleth map (CartoDB Dark Matter): all 319 tracts colored by risk
- Top-10 numbered pins with popup details
- Top-10 ranked list: expandable cards with all metrics
- Gemini alert generator: select tracts -> click Generate -> real AI alert
- Static fallback alerts for top-3 if Gemini unavailable
- Full data table (expandable)
- Run: streamlit run app/app.py -> http://localhost:8501

### Hour 5-9 Scoring (2026-08-29)
- Spatial join: 80,336 heatmap tiles -> 325 tracts, 0 unmatched
- env_params: 20 tracts, peak heat index (max of 24 hourly values)
- risk_score = 0.5*(0.4*norm_temp + 0.6*norm_hi_peak) + 0.5*norm_vuln
- Top-10 saved: data/top10_tracts.json

### Hour 2-5 Vulnerability (2026-08-29)
- CDC PLACES: 39,719 records, 40 measures, 993 tracts
- TIGER: 1,009 tract polygons
- Scored: data/vulnerability_scored.json

### Hour 0-2 API Validation (2026-08-29)
- Phoenix AZ 2024-07-15 CONFIRMED WORKING
- Cached: cache/heatmap_Phoenix_AZ_2024-07-15_result.json

---

## Final Top-10 Tracts

| Rank | Tract | Risk | Avg Temp | HI Peak | Vulnerability |
|------|-------|------|----------|---------|---------------|
| 1 | 04013981000 | 0.855 | 36.6C | 44.5C | 0.954 |
| 2 | 04013106801 | 0.757 | 36.3C | 45.4C | 0.646 |
| 3 | 04013106001 | 0.707 | 36.5C | 45.9C | 0.428 |
| 4 | 04013111501 | 0.682 | 36.6C | 45.6C | 0.420 |
| 5 | 04013111601 | 0.664 | 36.6C | 45.5C | 0.410 |
| 6 | 04013111502 | 0.657 | 36.6C | 45.6C | 0.377 |
| 7 | 04013113502 | 0.652 | 36.6C | 44.4C | 0.597 |
| 8 | 04013115200 | 0.650 | 36.2C | N/A | 0.498 |
| 9 | 04013111401 | 0.646 | 36.6C | N/A | 0.329 |
| 10 | 04013114302 | 0.642 | 35.9C | N/A | 0.600 |

---

## API Notes (confirmed - do not re-guess)

### FortyGuard /v1/heatmap - CONFIRMED
- POST https://api.fortyguard.com/v1/heatmap
- Header: api-key: FORTYGUARD_API_KEY
- date_time = OBJECT {"start_date":"2024-07-15","filter_type":3}
- Tile fields: average_temperature, min_temperature, max_temperature
- Cached: cache/heatmap_Phoenix_AZ_2024-07-15_result.json (80,336 tiles)

### FortyGuard /v1/env_params - CONFIRMED
- POST https://api.fortyguard.com/v1/env_params
- Required: latitude, longitude, temperature (C), date_time object
- analysis: ["heat_index_celsius","apparent_temperature_celsius","relative_humidity_percent"]
- Result path: data.result.locations[0].parameters.heat_index_celsius (array of 24 hourly values)
- Cached: cache/env_params_{geoid}.json (20 files)

### Gemini API - CONFIRMED WORKING
- Model: gemini-3.5-flash-lite
- POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent
- Header: x-goog-api-key: GEMINI_API_KEY
- Response: candidates[0].content.parts[0].text (IS the final answer, ignore thoughtSignature field)
- maxOutputTokens: 400, timeout: 30s

### CDC PLACES
- https://chronicdata.cdc.gov/resource/cwsq-ngmh.json
- Filter: StateAbbr=AZ&countyfips=04013&Year=2022
- All data cached: data/cdc_places_maricopa_all.json

---

## Environment

- Python 3.10+
- pip install -r requirements.txt
- .env: FORTYGUARD_API_KEY + GEMINI_API_KEY
- Run: streamlit run app/app.py
- Repo: https://github.com/Muhammadfaheen8988/HeatGuard
