"""
app/app.py  -  HeatGuard Alerts Dashboard
==========================================
Streamlit dashboard for the FortyGuard Hackathon 2026.
Shows a choropleth map + ranked risk list + Gemini-generated SMS alerts.

Data sources (all pre-computed, no live API calls on load):
  data/top10_tracts.json         - top-10 highest risk tracts
  data/merged_all_tracts.json    - all scored tracts (for full map)
  data/maricopa_tracts.geojson   - tract polygons for choropleth

Live API (on demand):
  Gemini API -> generates plain-language alert text per tract
"""

import json
import os
import math
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HeatGuard Alerts | Phoenix, AZ",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

DATA_DIR = Path("data")
DEMO_DATE = "July 15, 2024"
DEMO_CITY = "Phoenix, AZ"

RISK_COLORS = ["#FF0000", "#FF2D00", "#FF5A00", "#FF7700", "#FF9900",
               "#FFAA00", "#FFBB00", "#FFCC00", "#FFE100", "#FFFF00"]

# ─── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_top10():
    with open(DATA_DIR / "top10_tracts.json") as f:
        return json.load(f)

@st.cache_data
def load_all_merged():
    with open(DATA_DIR / "merged_all_tracts.json") as f:
        return json.load(f)

@st.cache_data
def load_tract_geojson():
    with open(DATA_DIR / "maricopa_tracts.geojson") as f:
        return json.load(f)

top10 = load_top10()
all_merged = load_all_merged()
tract_geojson = load_tract_geojson()

# Build lookup: GEOID -> merged record
merged_by_geoid = {r["tract_geoid"]: r for r in all_merged}
# Build lookup: GEOID -> risk_score for choropleth
risk_by_geoid = {r["tract_geoid"]: r.get("risk_score_final", 0) for r in all_merged}
max_risk = max(risk_by_geoid.values()) if risk_by_geoid else 1

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/HeatGuard-Alerts-red?style=for-the-badge", use_container_width=False)
    st.markdown("## 🌡️ HeatGuard Alerts")
    st.markdown("**Hyperlocal heat risk for {DEMO_CITY}**".format(DEMO_CITY=DEMO_CITY))
    st.markdown(f"📅 **Date:** {DEMO_DATE}")
    st.markdown("---")
    st.markdown("### 📊 Scoring Methodology")
    st.markdown("""
**Risk Score** = 50% Heat Severity + 50% Vulnerability

**Heat Severity:**
- 40% raw temperature (FortyGuard heatmap)
- 60% peak heat index (FortyGuard env_params)

**Vulnerability Index (CDC PLACES):**
- 40% elderly proxy (% teeth lost among 65+)
- 30% poverty proxy (% uninsured adults)
- 30% AC-access proxy (% utility shut-off threat)
""")
    st.markdown("---")
    st.caption("Data: FortyGuard API, CDC PLACES 2022, US Census TIGER")
    st.caption("Built for FortyGuard Hackathon 2026 · Track 04: Gov & Public Policy")

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid #e94560;
    }
    .main-header h1 { color: #ffffff; margin: 0; font-size: 2.2rem; }
    .main-header p  { color: #a0aec0; margin: 0.5rem 0 0; font-size: 1rem; }
    .alert-card {
        background: linear-gradient(135deg, #2d1b1b, #1a0a0a);
        border: 1px solid #e94560;
        border-left: 4px solid #e94560;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .alert-card h4 { color: #ff6b6b; margin: 0 0 0.3rem; }
    .alert-card p  { color: #cbd5e0; margin: 0; font-size: 0.9rem; line-height: 1.5; }
    .metric-card {
        background: #1a202c;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .risk-badge-1 { background: #ff0000; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .risk-badge-2 { background: #ff5500; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .risk-badge-3 { background: #ff9900; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🌡️ HeatGuard Alerts</h1>
    <p>Hyperlocal heat-risk intelligence for emergency managers · Phoenix, AZ · July 15, 2024</p>
</div>
""", unsafe_allow_html=True)

# ─── Top KPI strip ────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
top1 = top10[0] if top10 else {}
col1.metric("🏆 Highest Risk Score", f"{top1.get('risk_score_final', 0):.3f}", "Tract " + top1.get("tract_geoid","")[-6:])
col2.metric("🌡️ Peak Tile Temp", f"{top1.get('mean_temp_c', 0):.1f}°C", f"{top1.get('mean_temp_c', 0)*9/5+32:.1f}°F")
col3.metric("🔥 Peak Heat Index", f"{top1.get('heat_index_c', 0) or 0:.1f}°C", f"{(top1.get('heat_index_c', 0) or 0)*9/5+32:.1f}°F")
col4.metric("⚠️ Vulnerability", f"{top1.get('vulnerability_index', 0):.3f}", "Index 0-1")
col5.metric("📍 Tracts Analyzed", f"{len(all_merged):,}", "Maricopa County")

st.markdown("---")

# ─── Main layout: Map + Ranked list ──────────────────────────────────────────
map_col, list_col = st.columns([3, 2], gap="large")

with map_col:
    st.markdown("### 🗺️ Heat Risk Choropleth Map")
    st.caption("Color intensity = combined risk score (heat × vulnerability). Top-10 marked with pins.")

    # Build folium map
    m = folium.Map(
        location=[33.45, -112.07],
        zoom_start=11,
        tiles="CartoDB dark_matter"
    )

    # Choropleth: color all tracts by risk score
    def risk_to_color(score):
        if score is None or score == 0:
            return "#1a1a2e"
        intensity = min(score / max_risk, 1.0)
        r = int(255 * intensity)
        g = int(max(0, 80 * (1 - intensity)))
        b = 0
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    for feat in tract_geojson["features"]:
        geoid = feat["properties"]["GEOID"]
        score = risk_by_geoid.get(geoid, 0)
        color = risk_to_color(score)
        opacity = 0.1 + 0.7 * (score / max_risk) if score else 0.05
        folium.GeoJson(
            feat,
            style_function=lambda f, c=color, o=opacity: {
                "fillColor": c,
                "color": "#333333",
                "weight": 0.3,
                "fillOpacity": o,
            },
            tooltip=folium.Tooltip(
                f"Tract {geoid[-6:]}<br>Risk: {score:.3f}" if score else f"Tract {geoid[-6:]}"
            )
        ).add_to(m)

    # Mark top-10 with numbered pins
    for i, tract in enumerate(top10):
        lat = tract.get("centroid_lat")
        lon = tract.get("centroid_lon")
        if lat is None or lon is None:
            continue
        hi_str = f"{tract['heat_index_c']:.1f}°C" if tract.get("heat_index_c") else "N/A"
        popup_html = f"""
        <div style='font-family:sans-serif;width:200px'>
            <b style='color:#e94560'>#{i+1} · Tract {tract['tract_geoid'][-6:]}</b><br>
            Risk Score: <b>{tract['risk_score_final']:.3f}</b><br>
            Avg Temp: {tract['mean_temp_c']:.1f}°C | HI Peak: {hi_str}<br>
            Vulnerability: {tract['vulnerability_index']:.3f}<br>
            Population: {tract.get('total_population','N/A')}
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"#{i+1} · Risk {tract['risk_score_final']:.3f}",
            icon=folium.DivIcon(
                html=f"""<div style="
                    background:{'#ff0000' if i==0 else '#ff6600' if i<3 else '#ff9900'};
                    color:white;font-weight:bold;font-size:12px;
                    width:24px;height:24px;border-radius:50%;
                    display:flex;align-items:center;justify-content:center;
                    border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.5);
                ">{i+1}</div>""",
                icon_size=(24, 24),
                icon_anchor=(12, 12),
            )
        ).add_to(m)

    st_folium(m, height=500, use_container_width=True)

with list_col:
    st.markdown("### 🚨 Top 10 Highest Risk Tracts")
    st.caption(f"Ranked by combined heat + vulnerability score · {DEMO_DATE}")

    for i, tract in enumerate(top10):
        geoid = tract["tract_geoid"]
        risk = tract.get("risk_score_final", 0)
        temp = tract.get("mean_temp_c", 0)
        hi = tract.get("heat_index_c")
        vuln = tract.get("vulnerability_index", 0)
        pop = tract.get("total_population", "N/A")

        hi_str = f"{hi:.1f}°C ({hi*9/5+32:.0f}°F)" if hi else "N/A"
        temp_f = temp * 9/5 + 32

        badge_color = "#ff0000" if i == 0 else "#ff5500" if i < 3 else "#ff9900" if i < 6 else "#ffcc00"

        with st.expander(f"#{i+1}  Tract {geoid[-6:]}  —  Risk: {risk:.3f}", expanded=(i < 3)):
            c1, c2 = st.columns(2)
            c1.metric("Avg Temp", f"{temp:.1f}°C / {temp_f:.0f}°F")
            c2.metric("HI Peak", hi_str)
            c1.metric("Vulnerability", f"{vuln:.3f}")
            c2.metric("Population", f"{int(float(pop)) if pop and pop != 'N/A' else 'N/A':,}" if pop and pop != "N/A" else "N/A")

            st.markdown(f"""
            <div style="background:#1a202c;border-radius:6px;padding:0.6rem;margin-top:0.5rem;font-size:0.82rem;color:#a0aec0">
            🧓 Elderly proxy: <b>{tract.get('pct_age_65_proxy','N/A')}</b>%&nbsp;&nbsp;
            💸 Uninsured: <b>{tract.get('pct_poverty_proxy','N/A')}</b>%&nbsp;&nbsp;
            ⚡ Utility risk: <b>{tract.get('pct_no_ac_proxy','N/A')}</b>%
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# ─── Gemini Alert Generator ───────────────────────────────────────────────────
st.markdown("### 💬 AI-Generated Alert Messages")
st.caption("Gemini 2.0 Flash generates plain-language alerts for field teams and residents.")

STATIC_ALERTS = {
    "04013981000": "HEAT ALERT · Tract 981000 (SW Phoenix): Extreme risk today. Heat index peaks at 44.5°C (112°F). This area has Phoenix's highest concentration of elderly residents with limited AC access. Recommend immediate wellness checks at 200 W Jefferson St cooling center. Bring water and cooling supplies.",
    "04013106801": "HEAT ALERT · Tract 106801 (Central Phoenix): High risk. Heat index 45.4°C (114°F). Significant uninsured + utility-risk population. Deploy mobile cooling units to bus stops on W McDowell Rd. Check on residents in older housing stock.",
    "04013106001": "HEAT ALERT · Tract 106001 (Downtown Phoenix): Elevated risk. Peak heat index 45.9°C (115°F) — highest in the city today. Route additional outreach teams through this corridor before 10 AM.",
}

def generate_gemini_alert(tract):
    geoid = tract["tract_geoid"]
    temp = tract.get("mean_temp_c", 0)
    hi = tract.get("heat_index_c")
    vuln = tract.get("vulnerability_index", 0)
    elderly = tract.get("pct_age_65_proxy", "N/A")
    poverty = tract.get("pct_poverty_proxy", "N/A")
    no_ac = tract.get("pct_no_ac_proxy", "N/A")
    pop = tract.get("total_population", "N/A")

    prompt = f"""You are an emergency heat response coordinator for Phoenix, AZ.
Generate a concise, actionable SMS-style alert (max 3 sentences, plain English, no markdown)
for field teams about census tract {geoid}.

Data for July 15, 2024:
- Average temperature: {temp:.1f}°C ({temp*9/5+32:.0f}°F)
- Peak heat index: {f"{hi:.1f}°C ({hi*9/5+32:.0f}°F)" if hi else "N/A"}
- Vulnerability score: {vuln:.3f} / 1.0
- Elderly risk indicator: {elderly}%
- Uninsured adults: {poverty}%
- Utility shut-off risk: {no_ac}%
- Population: {pop}

Write the alert in the format: HEAT ALERT · [Location identifier]: [2-3 action sentences]."""

    try:
        headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 150, "temperature": 0.3}}
        r = requests.post(GEMINI_URL, headers=headers, json=body, timeout=10)
        if r.ok:
            data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
    except Exception as e:
        pass
    return STATIC_ALERTS.get(geoid, f"HEAT ALERT · Tract {geoid[-6:]}: Risk score {tract.get('risk_score_final',0):.3f}. Peak heat index {f'{hi:.1f}' + chr(176) + 'C' if hi else 'elevated'}. Prioritize wellness checks for elderly and uninsured residents.")

selected_tracts = st.multiselect(
    "Select tracts to generate alerts for:",
    options=[f"#{i+1} · {t['tract_geoid'][-6:]} (risk={t['risk_score_final']:.3f})" for i, t in enumerate(top10)],
    default=[f"#1 · {top10[0]['tract_geoid'][-6:]} (risk={top10[0]['risk_score_final']:.3f})"] if top10 else [],
    max_selections=5,
    help="Select up to 5 tracts. Gemini API generates alerts; static fallback if unavailable."
)

if selected_tracts and st.button("🔔 Generate Alerts", type="primary"):
    for sel in selected_tracts:
        rank = int(sel.split("·")[0].strip().replace("#","")) - 1
        tract = top10[rank]
        with st.spinner(f"Generating alert for Tract {tract['tract_geoid'][-6:]}..."):
            alert_text = generate_gemini_alert(tract)
        hi = tract.get("heat_index_c")
        hi_str = f"{hi:.1f}°C" if hi else "N/A"
        st.markdown(f"""
        <div class="alert-card">
            <h4>🚨 #{rank+1} · Tract {tract['tract_geoid'][-6:]} &nbsp;|&nbsp; Risk: {tract['risk_score_final']:.3f} &nbsp;|&nbsp; HI Peak: {hi_str}</h4>
            <p>{alert_text}</p>
        </div>
        """, unsafe_allow_html=True)

elif not selected_tracts:
    st.info("Select tracts above and click 'Generate Alerts' to produce Gemini-powered field alerts.")

# ─── Data Table ───────────────────────────────────────────────────────────────
with st.expander("📋 Full Top-10 Data Table"):
    import pandas as pd
    rows = []
    for i, t in enumerate(top10):
        hi = t.get("heat_index_c")
        rows.append({
            "Rank": i+1,
            "Tract GEOID": t["tract_geoid"],
            "Risk Score": round(t.get("risk_score_final", 0), 3),
            "Avg Temp (°C)": round(t.get("mean_temp_c", 0), 1),
            "HI Peak (°C)": round(hi, 1) if hi else None,
            "Vuln Index": round(t.get("vulnerability_index", 0), 3),
            "Elderly %": t.get("pct_age_65_proxy"),
            "Uninsured %": t.get("pct_poverty_proxy"),
            "Utility Risk %": t.get("pct_no_ac_proxy"),
            "Population": t.get("total_population"),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#4a5568;font-size:0.8rem;padding:1rem 0">
    ⚠️ <b>Disclaimer:</b> This is a demonstration system built for FortyGuard Hackathon 2026 using historical data (July 15, 2024).
    Not for operational emergency management use. &nbsp;|&nbsp;
    Data: FortyGuard API · CDC PLACES 2022 · US Census TIGER/Line &nbsp;|&nbsp;
    Built with Streamlit · Folium · Gemini 2.0 Flash
</div>
""", unsafe_allow_html=True)