"""
config.py -- HeatGuard Alerts
=============================
ALL config constants live here.

CONFIRMED WORKING COMBO (2026-08-29 validated):
  City: Phoenix, AZ | Date: 2024-07-15 | filter_type=3 | granularity=100
  activity_id: 1a368278-6c38-41d5-a60f-c5ef3396e112
  Result: Completed, tiles with average_temperature ~35.6C

KEY FINDING: date_time is an OBJECT not separate start_date/start_time fields.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# API KEYS
FORTYGUARD_API_KEY = os.getenv("FORTYGUARD_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# FORTYGUARD API - ALL CONFIRMED
FG_BASE_URL = "https://api.fortyguard.com"
FG_HEATMAP_ENDPOINT = "/v1/heatmap"
FG_ENV_PARAMS_ENDPOINT = "/v1/env_params"
FG_STATUS_ENDPOINT = "/v1/status"

# DEMO CITY / DATE - LOCKED
DEMO_CITY = "Phoenix, AZ"
DEMO_CITY_NAME_SHORT = "Phoenix"
DEMO_STATE_FIPS = "04"
DEMO_COUNTY_FIPS = "04013"
DEMO_DATE = "2024-07-15"
DEMO_START_TIME = "00:00"
DEMO_SNAPSHOT_LABEL = "July 15, 2024 (Historical)"

# PHOENIX AOI - CONFIRMED WORKING
DEMO_AOI = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-112.15, 33.37], [-111.85, 33.37],
                [-111.85, 33.63], [-112.15, 33.63],
                [-112.15, 33.37]
            ]]
        }
    }]
}

# FORTYGUARD REQUEST PARAMS
GRANULARITY = 100
FILTER_TYPE = 3
ANALYTIC_TYPE = "tcm"
POLL_INTERVAL_SECONDS = 10
POLL_MAX_RETRIES = 90

def make_date_time(start_date=None, filter_type=None, start_time=None):
    """Build the date_time object for FortyGuard API requests.
    Confirmed format: {"date_time": {"start_date": "2024-07-15", "filter_type": 3}}
    """
    dt = {"start_date": start_date or DEMO_DATE, "filter_type": filter_type or FILTER_TYPE}
    if start_time:
        dt["start_time"] = start_time
    return dt

# HEATMAP RESULT FIELDS (CONFIRMED from live response)
# data.result.map_data = GeoJSON FeatureCollection
# feature.properties: tile_id, average_temperature, min_temperature, max_temperature
HEATMAP_TEMP_FIELD = "average_temperature"
HEATMAP_MIN_FIELD = "min_temperature"
HEATMAP_MAX_FIELD = "max_temperature"

# ENV PARAMS FIELD NAMES (CONFIRMED from docs)
# Required: latitude, longitude, temperature (C), date_time
ENV_PARAMS_HEAT_INDEX_FIELD = "heat_index_celsius"
ENV_PARAMS_ANALYSIS_FIELDS = ["heat_index_celsius", "apparent_temperature_celsius", "relative_humidity_percent"]

# VULNERABILITY SCORING WEIGHTS - must sum to 1.0
W_AGE = 0.4
W_POVERTY = 0.3
W_AC = 0.3
assert abs(W_AGE + W_POVERTY + W_AC - 1.0) < 1e-9

# HEAT SEVERITY WEIGHTS - must sum to 1.0
W_TEMP = 0.4
W_HEATINDEX = 0.6
assert abs(W_TEMP + W_HEATINDEX - 1.0) < 1e-9

# FINAL RISK SCORE WEIGHTS - must sum to 1.0
W_HEAT = 0.5
W_VULN = 0.5
assert abs(W_HEAT + W_VULN - 1.0) < 1e-9

# ALERT THRESHOLDS
ALERT_HEAT_INDEX_THRESHOLD_C = 39.0
ALERT_VULN_THRESHOLD = 0.66

# COOLING CENTER (placeholder)
COOLING_CENTER_NAME = "Phoenix Civic Center Cooling Station"
COOLING_CENTER_ADDRESS = "200 W Jefferson St, Phoenix, AZ 85003"
COOLING_CLOSING_TIME = "10:00 PM"
DISCLAIMER_TEXT = "This is a simulated alert for demonstration purposes."

# GEMINI
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_TIMEOUT_SECONDS = 8

# PATHS
CACHE_DIR = "cache"
DATA_DIR = "data"
TOP_N_TRACTS = 10

# CENSUS / CDC
CENSUS_API_BASE = "https://api.census.gov/data"
CENSUS_ACS_YEAR = "2022"
CDC_PLACES_BASE = "https://chronicdata.cdc.gov/resource"
CDC_PLACES_DATASET_ID = "cwsq-ngmh"
