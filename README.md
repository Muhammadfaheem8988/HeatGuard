# HeatGuard Alerts

**Vulnerability-Targeted Heat Early Warning System**  
FortyGuard Hackathon '26 | Track 04: Government & Public Policy | Track 07: Data Analysis & Visualization

---

## Problem

Extreme heat kills more people in the U.S. than any other weather hazard. But heat death is not random — it clusters in specific blocks among specific populations: elderly residents, low-income households without AC, and outdoor workers. Current city-wide heat warnings tell everyone "it's hot" but don't tell emergency managers *which 10 blocks* need a wellness check today.

**HeatGuard closes that gap** by fusing hyperlocal FortyGuard temperature data with CDC/Census vulnerability data to produce a ranked, explainable top-10 risk list — and simulates what targeted alerts to those blocks would actually say.

---

## Live Demo

*URL: [to be added after deployment]*

---

## How to Run

```bash
# 1. Clone
git clone https://github.com/Muhammadfaheem8988/HeatGuard.git
cd HeatGuard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env and fill in: FORTYGUARD_API_KEY and GEMINI_API_KEY

# 4. Run dashboard
streamlit run app/app.py
```

---

## AI Tool Disclosure

**Tools used to build this project:**
- Google Antigravity (Gemini/Claude) — used for PRD drafting, code scaffolding, and debugging

**AI used inside the shipped product:**
- **Google Gemini API (free tier)** — used at runtime to generate plain-language alert text from structured risk data (tract GEOID, heat index, vulnerability sub-scores). Static-template fallback on any API failure. This is a functional feature, not a build tool.

---

## API Proof-of-Use

### /v1/heatmap — Real Request & Response

```
[To be filled after Hour 0-2 API validation]
```

### /v1/env_params — Real Request & Response

```
[To be filled after Hour 0-2 API validation]
```

### CDC PLACES / Census ACS — Real Request & Response

```
[To be filled in Hour 2-5]
```

### Gemini API — Real Request & Response (Alert Generation)

```
[To be filled in Hour 9-14]
```

---

## Known Limitations

- Single city, single historical date (not live current data — see "empty tile" bug in PRD)
- "No AC" vulnerability proxy: [to be documented after ACS data pull]
- Cooling center info is illustrative (placeholder) — not sourced from a live municipal dataset
- No real alerts are sent — all alerts are simulated and labeled as such

---

## Architecture

```
FortyGuard /v1/heatmap  +  /v1/env_params
         +
CDC PLACES / Census ACS (tract-level vulnerability)
         |
     [Fusion Layer: spatial join heat tiles -> tracts]
         |
     [Scoring Engine: weighted risk_score per tract]
         |
     [Alert Engine: Gemini-generated plain-language alerts]
         |
     [Streamlit Dashboard: map + ranked list + alert feed]
```

---

*No API keys are committed to this repository. All secrets are in `.env` (git-ignored) or Streamlit Cloud secrets manager.*
