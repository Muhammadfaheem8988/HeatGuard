# PRD: HeatGuard Alerts — Vulnerability-Targeted Heat Early Warning System

**Hackathon:** FortyGuard Hackathon '26
**Primary Track:** Track 04 — Government & Public Policy
**Secondary Track:** Track 07 — Data Analysis & Visualization
**Status:** Build-ready
**Doc owner:** Team (fill in team name before submission)
**Last updated:** 29 August 2026

---

## 1. Overview & Problem Statement

Extreme heat kills more people in the U.S. every year than any other weather hazard combined — more than hurricanes, floods, and tornadoes. But heat death is not random. It clusters predictably in specific blocks and among specific populations: elderly residents living alone, outdoor and delivery workers, and low-income households without reliable access to air conditioning. A block with mostly young, air-conditioned households at 41°C heat index is a discomfort. The same 41°C in a block of elderly residents in un-cooled housing is a mass-casualty risk.

**The gap:** Current heat warnings (NWS Heat Advisories, city-wide alerts) are issued at the metro or county level. They tell an entire city of two million people "it's hot today," but they do nothing to tell an emergency manager, a public health department, or a community organization *which ten blocks* need a wellness check today, or *which alert message* should go to a household with an elderly resident versus a household with an outdoor worker.

**Who is affected:**
- **Elderly residents** (65+), especially those living alone — heat stroke risk rises sharply with age, and social isolation delays intervention.
- **Low-income households without air conditioning** — cannot self-mitigate even when they know it's hot.
- **Outdoor workers** (construction, delivery, agriculture) — exposed regardless of indoor conditions at home.
- **City agencies and community organizations** — have limited staff/resources for wellness checks and cooling-center outreach, and no tool to prioritize *where* to send them first.

**Why current solutions fall short:** They optimize for *coverage* (reach everyone) rather than *targeting* (reach the highest-risk few first, with the resources available). HeatGuard Alerts closes that gap by fusing hyperlocal temperature data with public vulnerability data to produce a ranked, actionable, block-level risk list — and by simulating what a targeted alert to that block would actually say.

---

## 2. Goals & Success Metrics

### Goals
1. Demonstrate that hyperlocal heat data (FortyGuard) + public vulnerability data (CDC/Census) can be fused into a single, defensible risk score at the census-tract level.
2. Produce a ranked, explainable "top 10 highest-risk blocks" list for a real U.S. city.
3. Simulate a realistic, plain-language, targeted alert workflow that a city agency could plausibly adopt.
4. Ship a working, deployed, judge-testable demo within the hackathon window.

### Definition of "Done"
- [ ] Live, publicly accessible dashboard showing a real city's heat + vulnerability map.
- [ ] Ranked top-10 list with visible score breakdown (temp contribution vs. vulnerability contribution).
- [ ] At least 3–5 simulated alerts visible in a live feed panel, generated from real fused data (not hardcoded copy).
- [ ] README with one real, saved request/response example from `/v1/heatmap`, one from `/v1/env_params`, and one from the CDC/Census data pull.
- [ ] Demo video (≤3 min) narrating the problem, the fusion, and the output.
- [ ] Deployed and verified to load cold (fresh incognito window) before submission.

### Measurable claim for the demo
We cannot access real heat-mortality or ER-visit data inside the hackathon window, so **do not claim** a specific measured outcome like "reduces ER visits by X%." Instead, frame the claim as a **defensible estimate**, clearly labeled as such:

> "Our model flags the ~5% of census tracts in [City] carrying the highest combined heat-and-vulnerability score. National CDC data attributes a large share of heat-related deaths to a small number of high-vulnerability tracts, so **targeting outreach to this top 5% is a reasonable, resource-efficient starting point for a city with limited wellness-check capacity** — this is a prioritization estimate, not a validated health outcome."

This framing is honest, still compelling, and matches Impact & Relevance judging criteria without overclaiming.

---

## 3. Target Users / Stakeholders

| User | Role | What they need from HeatGuard |
|---|---|---|
| City Emergency Management Office | Primary buyer/adopter | A daily-refreshable, block-level priority list to direct wellness checks and cooling-center outreach during heat events |
| Public Health Department | Secondary adopter | Evidence-based targeting for heat-illness prevention campaigns |
| Community Organizations (e.g., senior services, mutual aid) | Field operator | A simple, non-technical view of "who to check on today" |
| Hackathon Judges | Evaluator | Clear evidence of real API usage, a real problem, a measurable/defensible claim, and a working live demo |

---

## 4. Scope

### In Scope
- Single U.S. city, single historical date/time window (chosen for API reliability — see Section 8).
- Heatmap ingestion via `/v1/heatmap`.
- Point-level heat index via `/v1/env_params`.
- Public vulnerability data via CDC PLACES or Census ACS (tract-level).
- Spatial join of heat tiles to census tracts.
- Weighted, tunable risk scoring algorithm.
- Top-10 ranked risk list.
- Simulated (not real) SMS-style alert generation and a live feed UI.
- Single-page responsive dashboard (map + ranked list + alert feed).
- README with proof-of-API-use (real request/response for each external API).

### Out of Scope (this build)
- **Real SMS/email sending** — alerts are simulated and displayed in-app only. No Twilio, no real dispatch.
- Multi-city support (single city for the hackathon demo; architecture should not *prevent* this later, but it is not built now).
- User authentication / login.
- Historical trend analysis or forecasting beyond the single demo window.
- Real-time/live current-hour data (given the known empty-tile bug — see Section 8, we deliberately use a verified historical window).
- Mobile native app (responsive web only).
- Any claim of validated health-outcome reduction (see Section 2).

---

## 5. User Stories

1. **As a dashboard viewer (city official),** I want to see a color-coded map of heat + vulnerability risk across the city, so that I can visually identify hot spots without reading raw data tables.
2. **As a risk analyst,** I want to see the top 10 highest-risk blocks ranked with a visible score breakdown (temperature contribution vs. vulnerability contribution), so that I can understand *why* a block is flagged, not just *that* it is.
3. **As an alert reviewer,** I want to see a live feed of simulated, plain-language alerts generated from the actual fused data, so that I can evaluate whether the message content and targeting logic would be usable in a real deployment.
4. **As a hackathon judge,** I want to see a real, saved API request and response for every external data source used, so that I can verify the project genuinely integrates with the FortyGuard Temperature API (and not mocked/fabricated data).
5. **As a mobile user,** I want the dashboard to remain legible and usable on a phone screen, so that field staff could plausibly use this during a heat event.

---

## 6. System Architecture

### Proposed Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | **Streamlit** (fastest path to a deployable, interactive dashboard) with a Leaflet/Mapbox component (e.g., `streamlit-folium` or `pydeck`) | Fastest to build + deploy within hackathon time budget; Streamlit Cloud is a listed acceptable deploy target |
| Backend / data processing | **Python** (pandas, geopandas, requests) | Standard geospatial fusion stack; team likely already fluent |
| Data layer | Flat files / in-memory (Parquet or GeoJSON cached to disk after API pulls) | No need for a database at this scale (single city, single time window); avoids infra risk |
| External APIs | FortyGuard `/v1/heatmap`, `/v1/env_params`; CDC PLACES or Census ACS (REST, no key); **Google Gemini API (free tier)** for alert text generation | Required by hackathon rules; CDC/Census require no auth, reducing integration risk; Gemini adds a genuine LLM/AI component (see Section 9.1) |
| Deployment | Streamlit Community Cloud (fallback: Render) | Simplest, listed-as-acceptable, free-tier deploy path |

> **Alternative stack (if team prefers):** FastAPI backend + React/Leaflet frontend, deployed backend on Render and frontend on Vercel. Use this only if the team already has this stack ready to go — do not introduce a new stack under time pressure. Default recommendation is Streamlit for speed.

### Data Flow

```
┌─────────────────────┐     ┌──────────────────────┐     ┌───────────────────────┐
│ FortyGuard           │     │ FortyGuard            │     │ CDC PLACES / Census    │
│ /v1/heatmap          │     │ /v1/env_params        │     │ ACS (tract-level)      │
│ (tile grid, filter_  │     │ (heat index at        │     │ (age65+, poverty,      │
│  type=3, full day)   │     │  representative pts)  │     │  no-AC housing %)      │
└──────────┬───────────┘     └──────────┬────────────┘     └───────────┬────────────┘
           │                            │                              │
           └──────────────┬─────────────┴──────────────┬───────────────┘
                           ▼                            ▼
                 ┌────────────────────────────────────────────┐
                 │           FUSION LAYER (Python)             │
                 │  - Spatial join: heat tiles → census tracts │
                 │  - Attach heat_index per tract               │
                 │  - Attach vulnerability sub-scores per tract│
                 └───────────────────────┬──────────────────────┘
                                         ▼
                 ┌────────────────────────────────────────────┐
                 │            SCORING ENGINE                   │
                 │  risk_score = f(temp, heat_index, vuln_idx) │
                 │  → rank all tracts, identify top 10         │
                 └───────────────────────┬──────────────────────┘
                                         ▼
                 ┌────────────────────────────────────────────┐
                 │        ALERT SIMULATION ENGINE              │
                 │  IF heat_index > threshold AND               │
                 │     vuln_index > threshold                   │
                 │  → call Gemini API with structured risk data │
                 │  → Gemini returns plain-language alert text  │
                 │  → fallback to static template on API error   │
                 │  → log to alert feed                          │
                 └───────────────────────┬──────────────────────┘
                                         ▼
                 ┌────────────────────────────────────────────┐
                 │         DASHBOARD (Streamlit)               │
                 │  [ Map ]   [ Ranked List ]   [ Alert Feed ] │
                 └────────────────────────────────────────────┘
```

---

## 7. Data Model

### 7.1 Heatmap Tile Record (from `/v1/heatmap`)

| Field | Type | Description |
|---|---|---|
| `tile_id` | string | Unique tile identifier from API response |
| `lat` | float | Tile centroid latitude |
| `lon` | float | Tile centroid longitude |
| `temperature_c` | float | 2m air temperature, °C |
| `date` | string (ISO date) | Date of measurement |
| `hour` | int (0–23) | Hour of measurement (derive from request `start_time` per hour if `filter_type=3` returns a full-day series — confirm exact response shape during Hour 0–2, see Section 8) |
| `granularity_m` | int | Tile granularity requested (e.g., 60, 100) |

### 7.2 Vulnerability Tract Record (from CDC PLACES / Census ACS)

| Field | Type | Description |
|---|---|---|
| `tract_geoid` | string | Census tract FIPS/GEOID |
| `tract_geometry` | GeoJSON polygon | Tract boundary (from TIGER/Line or Census geometry API) |
| `pct_age_65_plus` | float (0–100) | % of population 65+ |
| `pct_poverty` | float (0–100) | % of population below poverty line |
| `pct_no_ac` | float (0–100) | % of housing units without air conditioning (from ACS housing characteristics, or a proxy field — see Section 8 quirks) |

### 7.3 Fused Dataset Record (tile ↔ tract joined)

| Field | Type | Description |
|---|---|---|
| `tile_id` | string | From heatmap |
| `tract_geoid` | string | From spatial join |
| `temperature_c` | float | From heatmap |
| `heat_index_c` | float | From `/v1/env_params`, matched by nearest representative point + same timestamp |
| `pct_age_65_plus` | float | From vulnerability data |
| `pct_poverty` | float | From vulnerability data |
| `pct_no_ac` | float | From vulnerability data |
| `vulnerability_index` | float (0–1, normalized) | Computed — see Section 9 |

### 7.4 Risk Score Record

| Field | Type | Description |
|---|---|---|
| `tract_geoid` | string | Tract identifier |
| `risk_score` | float (0–1) | Final combined score — see Section 9 |
| `temp_contribution` | float | Portion of score attributable to heat |
| `vuln_contribution` | float | Portion of score attributable to vulnerability |
| `rank` | int | 1 = highest risk |
| `centroid_lat` / `centroid_lon` | float | For map display |

### 7.5 Alert Record

| Field | Type | Description |
|---|---|---|
| `alert_id` | string (UUID) | Unique ID |
| `tract_geoid` | string | Target tract |
| `heat_index_c` | float | Trigger value |
| `vulnerability_index` | float | Trigger value |
| `message` | string | Generated plain-language alert text |
| `timestamp_generated` | ISO datetime | When the simulation generated it |
| `status` | enum: `simulated` | Always `simulated` in this build — never `sent` |
| `generation_method` | enum: `gemini` \| `fallback_template` | Which path produced `message` — see Section 9.1 |

---

## 8. API Integration Details

### 8.1 `/v1/heatmap` (FortyGuard)

| Parameter | Required | Notes |
|---|---|---|
| `polygon_aoi` | Yes | GeoJSON FeatureCollection, `[lon, lat]` order, ring must close (first = last point) |
| `start_date` | Yes | Must be between `2021-01-01` and today; use a **historical** date, not today's date |
| `start_time` | Yes | Interpreted as local time at the AOI |
| `filter_type` | Yes | Use `3` (entire day) to get a diurnal curve; `1` = single hour, `2` = hour range, `4` = date range |
| `granularity` | Yes | e.g., `60` or `100` meters — start with a coarser value (100m) to reduce tile count and credit cost |
| `analytic_type` | No (defaults exist) | Use `tcm` (temperature snapshot per tile, °C) for this build |
| Auth | Header `api-key: YOUR_KEY` | Each team member uses their own key |
| Workflow | Async | POST returns `activity_id` → poll `GET /v1/status/{activity_id}` until `Completed` |
| AOI limit | ~130 km² (50 mi²) | Keep polygon within this |

**Known quirk — "empty tile" bug:** Current/very-recent-hour requests have returned `n_cells: 0` / `features: []` even with valid auth and a valid U.S. polygon (confirmed by other teams in the hackathon Slack). **Mitigation:** use a verified historical date (e.g., a summer 2024 or 2025 date — **to confirm during Hour 0–2** by testing a known-good historical date/time/AOI combo before building anything downstream). Do not build the fusion/scoring layer against an untested request — validate the exact date/time/polygon combination first and lock it in as a config constant.

### 8.2 `/v1/env_params` (FortyGuard)

| Parameter | Required | Notes |
|---|---|---|
| `lat`, `lon` | Yes | Single point, not a polygon |
| `start_date`, `start_time` | Yes | Must match the heatmap request's date/time to allow correlation |
| Auth | Header `api-key` | Same key as heatmap |
| Response | Heat index, AQI, solar irradiance, etc. | Confirm exact field names against a live test call — response structure should be checked directly (paste API key into the docs page and inspect a real response) rather than assumed |
| Workflow | Async | Same submit → poll pattern as heatmap |

**Usage plan:** call this for 2–3 representative points per top-risk tract (e.g., tract centroid + 1–2 additional points) rather than every tile, to conserve API credits.

### 8.3 CDC PLACES or Census ACS (vulnerability data)

| Parameter | Required | Notes |
|---|---|---|
| Geography | Census tract, filtered to the target city/county FIPS | Both CDC PLACES and Census ACS support tract-level queries |
| Auth | **None required** | Public REST API, no API key |
| Fields needed | `% age 65+`, `% below poverty`, housing/AC proxy | ACS table `B25040` (house heating fuel) does not directly give AC; ACS does **not** have a clean "no AC" variable in most releases — **to confirm during Hour 2–5**: either use CDC PLACES' heat-vulnerability-adjacent measures, or substitute a documented proxy (e.g., housing built pre-1980 + income, or a state/local open-data AC-access dataset if the chosen city publishes one) and clearly document the substitution in the README |
| Rate limits | Census API: generous but not unlimited; cache after first pull | No auth needed but be a good citizen — pull once, cache to disk/Parquet |

### 8.4 Google Gemini API (free tier) — Alert Text Generation

| Parameter | Required | Notes |
|---|---|---|
| Model | `gemini-2.0-flash` or `gemini-1.5-flash` (confirm current free-tier model name at build time — Google renames/updates these; check `ai.google.dev` for the current free-tier model list) | Use the smallest/fastest free-tier model — this is short text generation, not a task that needs a large model |
| Auth | API key via `x-goog-api-key` header or `?key=` query param (Google AI Studio issues free-tier keys at `aistudio.google.com`) | Separate from FortyGuard key — keep in its own `.env` variable, e.g. `GEMINI_API_KEY` |
| Endpoint shape | `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` | Confirm exact path/version against current docs at build time — Google's API versioning changes periodically |
| Rate limits (free tier) | Low but sufficient for this use case (typically single-digit requests per minute, low thousands per day — **confirm current limits at aistudio.google.com before the demo**, free-tier limits change) | You only need one call per triggered alert (max ~10–15 calls for a top-10 list), so free-tier limits are not a practical constraint here |
| Input | A structured prompt containing: tract GEOID/name, `heat_index_c`, `vulnerability_index`, contributing factors (age/poverty/AC), and a placeholder cooling-center name | See prompt template in Section 9.1 |
| Output | Plain-language alert text (2–4 sentences) | Must be parsed as plain text; no special output schema required for this build |
| Failure handling | **Required fallback:** if the Gemini call fails, times out, or returns an error, fall back to the static template from Section 9 immediately — never let a live demo alert panel show an error or blank message | This is a demo-reliability requirement, not optional |

### 8.5 Credit & Rate-Limit Notes (from hackathon platform)
- Failed API tasks are free — only successful completions consume credits.
- Cache every successful response locally; never re-request the same area/date/time combo.
- Test on a single small polygon before scaling to the full city AOI.

---

## 9. Scoring Algorithm Spec

### Step 1 — Normalize each sub-factor to 0–1 (min-max normalization across all tracts in the study area)

```
norm(x) = (x - min(x)) / (max(x) - min(x))
```

Applied to: `temperature_c`, `heat_index_c`, `pct_age_65_plus`, `pct_poverty`, `pct_no_ac`.

### Step 2 — Compute Vulnerability Index (per tract)

```
vulnerability_index = (w_age * norm(pct_age_65_plus))
                     + (w_poverty * norm(pct_poverty))
                     + (w_ac * norm(pct_no_ac))
```

| Weight | Placeholder default | Notes |
|---|---|---|
| `w_age` | 0.4 | Age is the strongest documented heat-mortality risk factor |
| `w_poverty` | 0.3 | Proxy for reduced adaptive capacity |
| `w_ac` | 0.3 | Direct mitigation-access factor |

*(Weights are tunable — expose as constants at the top of the scoring module so they can be adjusted without touching logic. Weights must sum to 1.0.)*

### Step 3 — Compute Heat Severity Index (per tract)

```
heat_severity = (w_temp * norm(temperature_c)) + (w_heatindex * norm(heat_index_c))
```

| Weight | Placeholder default |
|---|---|
| `w_temp` | 0.4 |
| `w_heatindex` | 0.6 (heat index is more human-relevant than raw air temp, so weighted higher) |

### Step 4 — Compute Final Risk Score

```
risk_score = (w_heat * heat_severity) + (w_vuln * vulnerability_index)
```

| Weight | Placeholder default |
|---|---|
| `w_heat` | 0.5 |
| `w_vuln` | 0.5 |

*(Equal weighting by default — defensible as a neutral starting point. Document this choice explicitly in the README/demo as a tunable parameter, not a scientifically derived constant.)*

### Step 5 — Rank

Sort all tracts descending by `risk_score`; assign `rank` 1..N; take top 10 for the ranked list panel; flag top 5% for the "priority outreach" framing described in Section 2.

### Alert Trigger Logic

```
IF heat_index_c > ALERT_HEAT_INDEX_THRESHOLD (default: 39°C / ~103°F)
   AND vulnerability_index > ALERT_VULN_THRESHOLD (default: top-tertile, i.e. > 0.66)
THEN generate_alert(tract)
```

Both thresholds are named constants, adjustable at the top of the alert module.

### Alert Message Generation — Primary Path (Gemini) + Fallback

Alert text is generated by calling the Gemini API with the tract's structured risk data (Section 9.1), rather than filling a single hardcoded template for every alert. This produces varied, context-appropriate language (e.g., an alert for a tract driven mostly by elderly population reads differently than one driven mostly by lack of AC), which is both more realistic and a legitimate use of an LLM in the product itself.

**Static fallback template** (used only if the Gemini call fails/times out — see Section 8.4):

```
"Heat index {heat_index_c}°C in your area — check on elderly neighbors.
Nearest cooling center: {cooling_center_name} (open until {closing_time}).
This is a simulated alert for demonstration purposes."
```

*(Cooling center name/hours can be a static placeholder for the demo city, clearly labeled as illustrative — do not fabricate real operating hours for a real facility without a source; use a generic placeholder like "City Cooling Center — Main St" if no verified source is available.)*

Every alert record (Section 7.5) should store which path generated it (`generation_method: "gemini"` or `"fallback_template"`) so this is transparent and debuggable during the demo.

### 9.1 Gemini Alert-Text Integration Spec

**Prompt template** (structured, deterministic inputs → natural-language output):

```
You are generating a short public heat-safety alert for a city emergency
management dashboard. Use the data below. Keep it to 2–4 sentences,
plain language, no medical jargon, no alarmism. Always end by naming the
cooling center and its hours. Always include the disclaimer sentence
exactly as given.

Tract: {tract_geoid} ({city_name})
Heat index: {heat_index_c}°C
Primary risk driver(s): {top_contributing_factors}
  (e.g., "high % of residents 65+", "low AC access", "high poverty rate")
Nearest cooling center: {cooling_center_name}, open until {closing_time}
Disclaimer to include verbatim: "This is a simulated alert for demonstration purposes."

Output only the alert message text. No preamble, no markdown, no quotation marks.
```

**Call pattern:**
1. Build the prompt from the fused risk record (Section 7.4) for each tract that crosses the alert threshold (Section 9, Alert Trigger Logic).
2. Call Gemini with a short timeout (e.g., 5–8 seconds).
3. On success → store returned text as `message`, `generation_method: "gemini"`.
4. On any failure (timeout, error, empty response, content filter block) → build `message` from the static template, `generation_method: "fallback_template"`.
5. Never block the dashboard load on Gemini latency for more than a few seconds total — if generating all alerts synchronously is too slow, generate them once at data-load time and cache the results for the demo session (this data is static/historical for the demo anyway — no need to regenerate on every page refresh).

**Cost/rate safety:** cache generated alert text alongside the rest of the fused dataset (e.g., in the same Parquet/JSON cache from Section 6) so redeploying or reloading the demo doesn't re-trigger API calls unnecessarily and doesn't risk hitting free-tier limits mid-demo.

---

## 10. UI/UX Requirements

### Layout (single page, top to bottom on mobile / left-right on desktop)

1. **Header bar:** Project name, city name + date/time of the analyzed snapshot (clearly labeled as historical/demo data, not live).
2. **Map panel (primary, largest element):**
   - Choropleth or tile overlay, red-scale color ramp (light yellow → deep red) representing `risk_score`.
   - Clicking a tile/tract opens a detail popup: tract GEOID, temperature, heat index, vulnerability sub-scores, final risk score.
3. **Ranked list panel (sidebar on desktop, below map on mobile):**
   - Top 10 tracts, each row: rank, tract name/GEOID, risk score, small bar showing temp-contribution vs. vulnerability-contribution split.
4. **Alert feed panel (sidebar or bottom section):**
   - Live-updating (or generated-on-load) list of simulated alerts, newest first.
   - Each entry: timestamp, tract, message text, a visible "SIMULATED — NOT SENT" badge.

### Color Scheme
- Risk scale: light yellow (`#FFF3CD`) → orange (`#FD7E14`) → deep red (`#C0392B`) for high risk.
- Alert badges: red badge, white text, label "SIMULATED".
- Keep the rest of the UI neutral (white/light grey background, dark text) so the red risk signal stands out.

### Responsive Behavior
- Desktop: map (≈65% width) + right sidebar (ranked list above, alert feed below).
- Mobile: stacked vertically — map first, then ranked list (collapsed/scrollable), then alert feed (collapsed/scrollable).
- Test at minimum at 375px (mobile) and 1280px (desktop) widths.

### Interactions
- Click tile/tract → detail popup.
- Optional (stretch, not required): slider to adjust alert threshold live and see the alert feed/ranked list update.

---

## 11. Milestones & Timeline

| Window | Task |
|---|---|
| **Hr 0–2** | Confirm a working city/date/time/AOI combo against `/v1/heatmap` (avoid empty-tile bug); lock this as a config constant. Confirm `/v1/env_params` response shape with one live test call. |
| **Hr 2–5** | Pull and clean CDC PLACES / Census ACS vulnerability data for the chosen city at tract level; resolve the "no AC" field/proxy question; cache to disk. |
| **Hr 5–9** | Spatial join heat tiles → tracts; pull `/v1/env_params` for representative points; implement scoring algorithm (Section 9); produce ranked list. |
| **Hr 9–14** | Build dashboard: map + ranked list + mock alert feed (Section 10). |
| **Hr 14–16** | Save one real request/response pair from each external API into `README.md`. |
| **Hr 16–18** | Deploy to Streamlit Cloud (or Render); test cold in a fresh incognito window. |
| **Hr 18–20** | Record 3-minute demo video (voiceover required; show it working, not slides). |
| **Hr 20–22** | Complete submission form: track selection, AI-tool disclosure, both team members' API keys, links. |
| **Buffer** | Reserve 2+ hours before the deadline for redeploy/fix issues (e.g., sleeping free-tier host). |

---

## 12. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| `/v1/heatmap` returns empty tiles for current/recent dates | Confirmed occurring for other teams | Use a verified historical date locked in during Hour 0–2; never rely on "today" for the demo |
| ACS/CDC has no clean "no AC" variable | Likely | Use a documented proxy (pre-1980 housing stock + income) or a city-specific open dataset if available; disclose the substitution explicitly in README and demo narration |
| Tract-level vulnerability data doesn't align cleanly with tile-level heat grid | Moderate | Aggregate heat tiles up to tract level (mean temp/heat index per tract) rather than trying to force tract data down to tile level — simpler and more defensible |
| API credit exhaustion before demo is finished | Low-moderate | Cache every successful response; test on small polygons first; use `filter_type=3` only once per demo city/date, not repeatedly |
| Free-tier deploy host goes to sleep before judging | Moderate | Test cold in incognito immediately after deploy, and again right before the deadline; consider Render (less aggressive sleep than some free tiers) as primary target |
| Overclaiming health impact (e.g., unverifiable ER-visit reduction %) | Reputational | Use the explicitly-hedged framing in Section 2; never state a specific outcome number without a cited source |
| Running out of time for the alert-simulation polish | Moderate | Build map + ranked list first (core value); alert feed can start as a simple rule-based list generated at load time — real-time "live" updating is a nice-to-have, not required |
| `/v1/env_params` field names differ from assumptions in this PRD | Low-moderate | Confirm via one live test call in Hour 0–2 before writing downstream code that assumes specific field names |
| Gemini API call fails, times out, or is rate-limited during the live demo | Low-moderate | Static fallback template (Section 9.1) is mandatory, not optional; pre-generate and cache all alert text once during build so the live demo never makes a Gemini call in real time |
| Gemini free-tier model name/endpoint changes before build time | Low | Confirm exact model name and endpoint at `ai.google.dev` / `aistudio.google.com` during Hour 0–2, alongside the other API confirmations |

---

## 13. Out-of-Scope / Future Work

- Real SMS/email dispatch integration (e.g., Twilio) for actual alert delivery.
- Multi-city, multi-state support with a city selector.
- Historical trend analysis (e.g., risk score over multiple past heatwaves).
- Predictive forecasting beyond the 12-hour FortyGuard forecast window.
- User authentication and role-based access (e.g., separate views for city staff vs. public).
- Integration with real cooling-center location/hours data via a verified municipal open-data feed.
- Validated correlation against real heat-mortality or ER-visit datasets (would require IRB/data-sharing agreements beyond hackathon scope).

---

## 14. Submission Requirements Checklist

- [ ] **Primary track:** Government & Public Policy (Track 04)
- [ ] **Secondary track tag(s):** Data Analysis & Visualization (Track 07) — up to 2 secondary tags allowed
- [ ] **AI tool disclosure:** List every AI tool used and what for. This has two distinct categories — be explicit about both:
  - *Tools used to build the project:* e.g., "Claude/ChatGPT used for PRD drafting, code scaffolding, and debugging"
  - *AI used inside the shipped product itself:* "Google Gemini API (free tier) used at runtime to generate plain-language alert text from structured risk data, with a static-template fallback on failure" — this is a functional feature, not a build tool, and should be called out as such since it's part of what judges are evaluating
- [ ] **API keys:** Both/all team members' FortyGuard API keys submitted together in the same field on the final form
- [ ] **README requirements:**
  - [ ] How to run the project from scratch
  - [ ] What doesn't work yet / known limitations
  - [ ] One real, saved `/v1/heatmap` request + response
  - [ ] One real, saved `/v1/env_params` request + response
  - [ ] One real, saved CDC PLACES / Census ACS request + response
  - [ ] One real, saved Gemini API request + response (prompt + generated alert text), to document the AI-generated-content feature
  - [ ] No API keys committed anywhere in the repo (use `.env`, git-ignored — this applies to `GEMINI_API_KEY` as much as the FortyGuard key)
- [ ] **Live demo:** Public URL, opens in incognito with no login/install, stays live through judging
- [ ] **Demo video:** ≤3 minutes, YouTube or Loom (unlisted OK), mandatory voiceover explaining what was built/how it works/what's being shown, slides do not count
- [ ] **Code repo:** GitHub/GitLab, `Hackathon-FG` (hackathon@fortyguard.com) added as collaborator if private
- [ ] **Submission form:** Submitted before 30 August 2026, 11:59 PM GST (resubmission allowed until deadline; latest entry counts)

---

## Appendix A — Config Constants to Confirm During Build (do not guess these)

| Constant | Status |
|---|---|
| Verified working `start_date` / `start_time` / `polygon_aoi` for `/v1/heatmap` (avoiding empty-tile bug) | **To confirm during Hour 0–2** |
| Exact `/v1/env_params` response field names (heat index field name, units) | **To confirm during Hour 0–2** via one live test call |
| Best available "no AC" data field or proxy for the chosen city | **To confirm during Hour 2–5** |
| Chosen demo city (recommend Phoenix or Houston — both are heat-relevant and likely well-covered in FortyGuard's U.S. dataset) | **To confirm during Hour 0–2**, lock in after first successful heatmap pull |
| Current Gemini free-tier model name and exact `generateContent` endpoint path | **To confirm during Hour 0–2** at `ai.google.dev` — do not hardcode a model name from memory, verify it's currently live on the free tier |
| Current Gemini free-tier rate limits (requests/minute, requests/day) | **To confirm during Hour 0–2** at `aistudio.google.com` — should be a non-issue at ~10–15 total calls, but verify before relying on it |

