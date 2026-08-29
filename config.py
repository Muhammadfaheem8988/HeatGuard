"""
config.py — HeatGuard Alerts
=============================
ALL config constants live here. After Hour 0-2 API validation, fill in the
DEMO_* constants below. Every other module imports from here — never hardcode
city/date/polygon anywhere else.

KEY PRINCIPLE: Weights sum to 1.0 within each group. Tunable without touching logic.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------
# API KEYS (from .env — never hardcode here)
# ---------------------------------------------
FORTYGUARD_API_KEY = os.getenv("FORTYGUARD_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ---------------------------------------------
# FORTYGUARD API BASE URL
# (confirm exact base URL from hackathon docs)
# ---------------------------------------------
FG_BASE_URL = "https://api.fortyguard.com"

# ---------------------------------------------
# DEMO CITY / DATE / AOI
# !! Lock these in after Hour 0-2 API validation !!
# ---------------------------------------------
DEMO_CITY = "Phoenix, AZ"        # Primary candidate (heat-relevant, PRD recommended)
DEMO_CITY_NAME_SHORT = "Phoenix"  # For display
DEMO_STATE_FIPS = "04"           # Arizona
DEMO_COUNTY_FIPS = "04013"       # Maricopa County (Phoenix metro)

# These are CANDIDATES — validate against /v1/heatmap before locking
# Phoenix summer 2024 during documented heat event
DEMO_DATE_CANDIDATE_1 = "2024-07-15"    # Primary: Phoenix July 2024 heat event
DEMO_DATE_CANDIDATE_2 = "2024-08-01"    # Backup candidate
DEMO_DATE_CANDIDATE_3 = "2023-07-18"    # Further backup: 2023 heat event
DEMO_START_TIME = "00:00"               # Start of day (filter_type=3 = full day)

# Lock this AFTER successful API validation:
DEMO_DATE = None  # e.g., "2024-07-15" — set after confirming non-empty tile response

# Phoenix central AOI polygon (approx 20km x 20km — well under 130km2 limit)
# [lon, lat] order. Ring MUST close (first == last point).
DEMO_AOI_PHOENIX = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-112.15, 33.37],   # SW corner
                    [-111.85, 33.37],   # SE corner
                    [-111.85, 33.63],   # NE corner
                    [-112.15, 33.63],   # NW corner
                    [-112.15, 33.37]    # Close ring (= SW corner)
                ]]
            }
        }
    ]
}

# Houston backup AOI (~20km x 20km central)
DEMO_AOI_HOUSTON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-95.50, 29.65],
                    [-95.20, 29.65],
                    [-95.20, 29.90],
                    [-95.50, 29.90],
                    [-95.50, 29.65]
                ]]
            }
        }
    ]
}

# ---------------------------------------------
# FORTYGUARD REQUEST PARAMS
# ---------------------------------------------
GRANULARITY = 100           # meters (start coarse for validation; can tighten later)
FILTER_TYPE = 3             # 3 = full day diurnal curve
ANALYTIC_TYPE = "tcm"       # temperature snapshot per tile, degrees C
POLL_INTERVAL_SECONDS = 10  # how often to poll /v1/status/{activity_id}
POLL_MAX_RETRIES = 60       # max 10 min wait (60 × 10s)

# ---------------------------------------------
# VULNERABILITY SCORING WEIGHTS
# Must sum to 1.0
# ---------------------------------------------
W_AGE = 0.4      # pct_age_65_plus (strongest heat-mortality risk factor)
W_POVERTY = 0.3  # pct_poverty (reduced adaptive capacity)
W_AC = 0.3       # pct_no_ac (direct mitigation access)

assert abs(W_AGE + W_POVERTY + W_AC - 1.0) < 1e-9, "Vulnerability weights must sum to 1.0"

# ---------------------------------------------
# HEAT SEVERITY WEIGHTS
# Must sum to 1.0
# ---------------------------------------------
W_TEMP = 0.4       # raw air temperature
W_HEATINDEX = 0.6  # heat index (more human-relevant, weighted higher)

assert abs(W_TEMP + W_HEATINDEX - 1.0) < 1e-9, "Heat severity weights must sum to 1.0"

# ---------------------------------------------
# FINAL RISK SCORE WEIGHTS
# Must sum to 1.0
# ---------------------------------------------
W_HEAT = 0.5  # heat severity contribution
W_VULN = 0.5  # vulnerability contribution (equal weighting — defensible neutral default)

assert abs(W_HEAT + W_VULN - 1.0) < 1e-9, "Risk score weights must sum to 1.0"

# ---------------------------------------------
# ALERT TRIGGER THRESHOLDS
# ---------------------------------------------
ALERT_HEAT_INDEX_THRESHOLD_C = 39.0   # ~103°F — NOAA "Danger" level
ALERT_VULN_THRESHOLD = 0.66            # Top tertile of vulnerability index

# ---------------------------------------------
# ALERT DEMO CONTENT (placeholders — clearly labeled as illustrative)
# ---------------------------------------------
COOLING_CENTER_NAME = "Phoenix Civic Center Cooling Station"
COOLING_CENTER_ADDRESS = "200 W Jefferson St, Phoenix, AZ 85003"
COOLING_CLOSING_TIME = "10:00 PM"
DISCLAIMER_TEXT = "This is a simulated alert for demonstration purposes."

# ---------------------------------------------
# GEMINI API CONFIG
# (confirm model name at aistudio.google.com before hardcoding)
# ---------------------------------------------
GEMINI_MODEL = "gemini-2.0-flash"     # Confirm this is current free-tier model
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_TIMEOUT_SECONDS = 8             # Max wait before fallback

# ---------------------------------------------
# CACHE DIRECTORY
# ---------------------------------------------
CACHE_DIR = "cache"

# ---------------------------------------------
# TOP N TRACTS FOR RANKED LIST
# ---------------------------------------------
TOP_N_TRACTS = 10

# ---------------------------------------------
# CENSUS / CDC CONSTANTS
# ---------------------------------------------
CENSUS_API_BASE = "https://api.census.gov/data"
CENSUS_ACS_YEAR = "2022"   # Most recent stable ACS 5-year
CDC_PLACES_BASE = "https://chronicdata.cdc.gov/resource"
CDC_PLACES_DATASET_ID = "cwsq-ngmh"  # CDC PLACES 2023 release (census tract level)
