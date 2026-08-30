"""
app/app.py  -  HeatGuard Alerts Dashboard
Run from project root: streamlit run app/app.py
"""

import json
import os
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="HeatGuard Alerts | Phoenix, AZ",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-3.5-flash-lite"
GEMINI_URL     = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

DATA_DIR  = Path("data")
DEMO_DATE = "July 15, 2024"
DEMO_CITY = "Phoenix, AZ"

TRACT_LABELS = {
    "04013981000": "SW Phoenix / Laveen",
    "04013106801": "Central Phoenix / Encanto",
    "04013106001": "Downtown Phoenix",
    "04013111501": "South Mountain",
    "04013111601": "South Mountain East",
    "04013111502": "South Mountain West",
    "04013113502": "Ahwatukee North",
    "04013115200": "Maryvale",
    "04013111401": "Laveen Village",
    "04013114302": "South Phoenix",
}

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

top10         = load_top10()
all_merged    = load_all_merged()
tract_geojson = load_tract_geojson()

risk_by_geoid = {r["tract_geoid"]: r.get("risk_score_final", 0) for r in all_merged}
max_risk      = max(risk_by_geoid.values()) if risk_by_geoid else 1

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 1.6rem 2rem; border-radius: 12px; margin-bottom: 0.8rem;
    border: 1px solid #e94560;
}
.main-header h1 { color: #fff; margin: 0; font-size: 2rem; }
.main-header p  { color: #a0aec0; margin: 0.4rem 0 0; font-size: 0.95rem; }
.api-badge {
    background: linear-gradient(90deg, #0f3460, #16213e);
    border: 1px solid #38a169; border-left: 4px solid #38a169;
    border-radius: 6px; padding: 0.5rem 1rem; margin-bottom: 1rem;
    color: #68d391; font-size: 0.85rem;
}
.alert-card {
    background: linear-gradient(135deg, #2d1b1b, #1a0a0a);
    border: 1px solid #e94560; border-left: 4px solid #e94560;
    border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
}
.alert-card h4 { color: #ff6b6b; margin: 0 0 0.4rem; font-size: 0.95rem; }
.alert-card p  { color: #cbd5e0; margin: 0; font-size: 0.9rem; line-height: 1.6; }
.sim-badge {
    display: inline-block; background: #c53030; color: white;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;
    padding: 2px 8px; border-radius: 4px; margin-bottom: 0.5rem;
}
.contrib-bar-wrap { margin-top: 0.6rem; }
.contrib-label { font-size: 0.75rem; color: #718096; margin-bottom: 2px; }
.contrib-bar { height: 8px; border-radius: 4px; display: flex; overflow: hidden; }
.contrib-heat { background: #e94560; }
.contrib-vuln { background: #805ad5; }
.contrib-legend { display: flex; gap: 12px; font-size: 0.72rem; color: #a0aec0; margin-top: 3px; }
.contrib-dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 3px; vertical-align: middle; }
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { display: none; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌡️ HeatGuard Alerts")
    st.caption(f"📅 {DEMO_DATE}  ·  {DEMO_CITY}")
    st.markdown("---")
    with st.expander("📊 Scoring Methodology", expanded=False):
        st.markdown("""
**Risk Score** = 50% Heat + 50% Vulnerability

**Heat Severity:**
- 40% avg tile temp (FortyGuard heatmap)
- 60% peak heat index (FortyGuard env_params)

**Vulnerability (CDC PLACES):**
- 40% elderly proxy (teeth loss 65+)
- 30% poverty proxy (% uninsured)
- 30% AC-access proxy (% utility shut-off)
""")
    st.markdown("---")
    st.caption("Data: FortyGuard API · CDC PLACES 2022 · US Census TIGER")
    st.caption("FortyGuard Hackathon 2026 · Track 04: Gov & Public Policy")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🌡️ HeatGuard Alerts</h1>
    <p>Hyperlocal heat-risk intelligence for emergency managers &nbsp;·&nbsp; Phoenix, AZ &nbsp;·&nbsp; July 15, 2024</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="api-badge">
    ✅ <b>Live data from FortyGuard Temperature API</b> — 80,336 heatmap tiles ingested ·
    env_params heat index pulled for top-20 tracts · See README for real request/response examples
</div>
""", unsafe_allow_html=True)

st.caption(
    "📅 Using a verified historical snapshot (Jul 2024) to guarantee complete "
    "FortyGuard tile coverage — recent/current dates intermittently return empty "
    "tiles, a known platform behavior. Scoring logic is fully date-agnostic."
)

# ── KPI strip — no delta arrows ──────────────────────────────────────────────
top1 = top10[0] if top10 else {}
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("🏆 Highest Risk Score",  f"{top1.get('risk_score_final', 0):.3f}", delta=None,
          help=f"Tract {top1.get('tract_geoid','')[-6:]} — highest combined risk in Maricopa County")
k2.metric("🌡️ Peak Tile Temp",      f"{top1.get('mean_temp_c', 0):.1f}°C",   delta=None,
          help=f"≈ {top1.get('mean_temp_c', 0)*9/5+32:.1f}°F — FortyGuard heatmap avg for top tract")
k3.metric("🔥 Peak Heat Index",     f"{(top1.get('heat_index_c') or 0):.1f}°C", delta=None,
          help=f"≈ {(top1.get('heat_index_c') or 0)*9/5+32:.1f}°F — FortyGuard env_params daily max")
k4.metric("⚠️ Vulnerability Index", f"{top1.get('vulnerability_index', 0):.3f}", delta=None,
          help="Normalized 0–1: elderly exposure + uninsured rate + utility shut-off risk")
k5.metric("📍 Tracts Analyzed",     f"{len(all_merged):,}", delta=None,
          help="Maricopa County census tracts with both heat and vulnerability scores")

st.markdown("---")

# ── Map + Ranked list ─────────────────────────────────────────────────────────
map_col, list_col = st.columns([3, 2], gap="large")

with map_col:
    st.markdown("### 🗺️ Heat Risk Choropleth Map")
    st.caption("Color intensity = combined risk score. Top-10 marked with numbered pins. Click a pin for details.")

    # P0 FIX: OpenStreetMap — keyless, no watermark
    m = folium.Map(location=[33.45, -112.07], zoom_start=11, tiles="OpenStreetMap")

    def risk_to_color(score):
        if not score:
            return "#222222"
        t = min(score / max_risk, 1.0)
        if t < 0.5:
            r = int(255 * (t / 0.5))
            g = int(200 * (1 - t / 0.5)) + 55
        else:
            r = 255
            g = int(100 * (1 - (t - 0.5) / 0.5))
        return "#{:02x}{:02x}00".format(r, max(0, g))

    for feat in tract_geojson["features"]:
        geoid  = feat["properties"]["GEOID"]
        score  = risk_by_geoid.get(geoid, 0)
        color  = risk_to_color(score)
        opac   = 0.08 + 0.65 * (score / max_risk) if score else 0.04
        folium.GeoJson(
            feat,
            style_function=lambda f, c=color, o=opac: {
                "fillColor": c, "color": "#555", "weight": 0.4, "fillOpacity": o
            },
            tooltip=folium.Tooltip(
                f"Tract {geoid[-6:]} · Risk: {score:.3f}" if score else f"Tract {geoid[-6:]}"
            )
        ).add_to(m)

    for i, tract in enumerate(top10):
        lat, lon = tract.get("centroid_lat"), tract.get("centroid_lon")
        if lat is None or lon is None:
            continue
        geoid  = tract["tract_geoid"]
        hi_str = f"{tract['heat_index_c']:.1f}°C" if tract.get("heat_index_c") else "N/A"
        label  = TRACT_LABELS.get(geoid, f"Tract {geoid[-6:]}")
        popup_html = f"""
        <div style='font-family:sans-serif;width:210px;font-size:13px'>
            <b style='color:#e94560'>#{i+1} · {label}</b><br>
            <span style='color:#888'>GEOID: {geoid}</span><br><br>
            Risk Score: <b>{tract['risk_score_final']:.3f}</b><br>
            Avg Temp: {tract['mean_temp_c']:.1f}°C &nbsp;|&nbsp; HI Peak: {hi_str}<br>
            Vulnerability: {tract['vulnerability_index']:.3f}<br>
            Population: {tract.get('total_population','N/A')}
        </div>"""
        pin_color = "#dd0000" if i == 0 else "#ee5500" if i < 3 else "#ff8800"
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=230),
            tooltip=f"#{i+1} · {label} · Risk {tract['risk_score_final']:.3f}",
            icon=folium.DivIcon(
                html=f'<div style="background:{pin_color};color:white;font-weight:bold;'
                     f'font-size:11px;width:22px;height:22px;border-radius:50%;'
                     f'display:flex;align-items:center;justify-content:center;'
                     f'border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.6);">{i+1}</div>',
                icon_size=(22, 22), icon_anchor=(11, 11),
            )
        ).add_to(m)

    st_folium(m, height=480, use_container_width=True)

    # P1-5: Color-scale legend
    st.markdown("""
    <div style="margin-top:0.5rem;padding:0.5rem 0.8rem;background:#1a202c;
                border-radius:8px;display:flex;align-items:center;gap:12px;">
        <span style="font-size:0.75rem;color:#a0aec0;white-space:nowrap;">Risk Score</span>
        <div style="flex:1;height:12px;border-radius:6px;
            background:linear-gradient(to right,#3b4500,#ffdc00,#ff8000,#ff0000);"></div>
        <span style="font-size:0.72rem;color:#718096;white-space:nowrap;">0.0 → 1.0</span>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.7rem;
                color:#718096;padding:2px 0.8rem 0;">
        <span>Low</span><span>Medium</span><span>High</span><span>Critical</span>
    </div>
    """, unsafe_allow_html=True)

with list_col:
    st.markdown("### 🚨 Top 10 Highest Risk Tracts")
    st.caption(f"Ranked by combined heat + vulnerability score · {DEMO_DATE}")

    for i, tract in enumerate(top10):
        geoid = tract["tract_geoid"]
        risk  = tract.get("risk_score_final", 0)
        temp  = tract.get("mean_temp_c", 0)
        hi    = tract.get("heat_index_c")
        vuln  = tract.get("vulnerability_index", 0)
        pop   = tract.get("total_population", "N/A")
        label = TRACT_LABELS.get(geoid, f"Tract {geoid[-6:]}")

        # P1-2: short format, °F in help tooltip — no truncation
        hi_str   = f"{hi:.1f}°C" if hi else "N/A"
        hi_help  = f"≈ {hi*9/5+32:.0f}°F daily peak" if hi else "env_params unavailable"
        avg_help = f"≈ {temp*9/5+32:.0f}°F (FortyGuard heatmap avg)"

        with st.expander(f"#{i+1}  {label}  —  {risk:.3f}", expanded=(i < 2)):
            c1, c2 = st.columns(2)
            c1.metric("Avg Temp",      f"{temp:.1f}°C", delta=None, help=avg_help)
            c2.metric("HI Peak",       hi_str,          delta=None, help=hi_help)
            c1.metric("Vulnerability", f"{vuln:.3f}",   delta=None, help="Composite 0–1 index")
            try:
                pop_val = f"{int(float(pop)):,}"
            except Exception:
                pop_val = "N/A"
            c2.metric("Population", pop_val, delta=None)

            st.markdown(f"""
            <div style="background:#1a202c;border-radius:6px;padding:0.5rem 0.7rem;
                        margin-top:0.4rem;font-size:0.8rem;color:#a0aec0">
            🧓 Elderly: <b>{tract.get('pct_age_65_proxy','?')}</b>%&nbsp;&nbsp;
            💸 Uninsured: <b>{tract.get('pct_poverty_proxy','?')}</b>%&nbsp;&nbsp;
            ⚡ Utility risk: <b>{tract.get('pct_no_ac_proxy','?')}</b>%
            </div>""", unsafe_allow_html=True)

            # P2-10: Heat vs Vuln contribution bar
            nh = tract.get("norm_heat_refined", tract.get("norm_heat", 0)) or 0
            nv = tract.get("norm_vuln", 0) or 0
            tot = (nh + nv) or 1
            hp = round(nh / tot * 100)
            vp = 100 - hp
            st.markdown(f"""
            <div class="contrib-bar-wrap">
                <div class="contrib-label">Risk contribution</div>
                <div class="contrib-bar">
                    <div class="contrib-heat" style="width:{hp}%"></div>
                    <div class="contrib-vuln" style="width:{vp}%"></div>
                </div>
                <div class="contrib-legend">
                    <span><span class="contrib-dot" style="background:#e94560"></span>Heat {hp}%</span>
                    <span><span class="contrib-dot" style="background:#805ad5"></span>Vuln {vp}%</span>
                </div>
            </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Alert generator ────────────────────────────────────────────────────────────
st.markdown("### 💬 AI-Generated Emergency Alerts")
st.caption("Gemini generates plain-language field alerts. Auto-loaded for highest-risk tract below.")

STATIC_ALERTS = {
    "04013981000": (
        "HEAT ALERT | SW Phoenix / Laveen (Tract 981000): Peak heat index 44.5°C (112°F) — "
        "highest vulnerability in Maricopa County (score 0.954). 63.9% of residents show elderly "
        "risk indicators with limited AC access. Deploy wellness teams immediately and route "
        "cooling-center transport to this zone first."
    ),
    "04013106801": (
        "HEAT ALERT | Central Phoenix / Encanto (Tract 106801): Heat index 45.4°C (114°F) with "
        "significant uninsured and utility-at-risk population. Deploy mobile cooling units to bus "
        "stops on W McDowell Rd and check residents in older housing stock."
    ),
    "04013106001": (
        "HEAT ALERT | Downtown Phoenix (Tract 106001): Peak heat index 45.9°C (115°F) — highest "
        "in county today. Route additional outreach teams through this corridor before 10 AM and "
        "ensure all cooling centers are open and staffed."
    ),
}

def generate_gemini_alert(tract):
    geoid   = tract["tract_geoid"]
    temp    = tract.get("mean_temp_c", 0)
    hi      = tract.get("heat_index_c")
    vuln    = tract.get("vulnerability_index", 0)
    elderly = tract.get("pct_age_65_proxy", "N/A")
    poverty = tract.get("pct_poverty_proxy", "N/A")
    no_ac   = tract.get("pct_no_ac_proxy", "N/A")
    pop     = tract.get("total_population", "N/A")
    label   = TRACT_LABELS.get(geoid, f"Tract {geoid[-6:]}")

    fallback = STATIC_ALERTS.get(geoid,
        f"HEAT ALERT | {label}: Risk {tract.get('risk_score_final',0):.3f}. "
        f"Peak HI {f'{hi:.1f}C' if hi else 'elevated'}. "
        "Prioritize wellness checks for elderly and uninsured residents.")

    if not GEMINI_API_KEY:
        return fallback
    try:
        prompt = (
            f"You are an emergency heat response coordinator for Phoenix, AZ.\n"
            f"Generate a concise, actionable SMS-style alert (max 3 sentences, plain English, no markdown) "
            f"for field teams about {label} (census tract {geoid}).\n\n"
            f"Data for July 15, 2024:\n"
            f"- Average temperature: {temp:.1f}C ({temp*9/5+32:.0f}F)\n"
            f"- Peak heat index: {f'{hi:.1f}C ({hi*9/5+32:.0f}F)' if hi else 'N/A'}\n"
            f"- Vulnerability score: {vuln:.3f} / 1.0\n"
            f"- Elderly risk: {elderly}%  |  Uninsured: {poverty}%  |  Utility risk: {no_ac}%\n"
            f"- Population: {pop}\n\n"
            f"Format: HEAT ALERT | {label}: [2-3 action sentences for field teams]."
        )
        headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
        body    = {"contents": [{"parts": [{"text": prompt}]}],
                   "generationConfig": {"maxOutputTokens": 400, "temperature": 0.4}}
        r = requests.post(GEMINI_URL, headers=headers, json=body, timeout=30)
        if r.ok:
            parts = r.json()["candidates"][0]["content"]["parts"]
            text  = " ".join(p["text"] for p in parts if p.get("text", "").strip()).strip()
            if text:
                return text
    except Exception:
        pass
    return fallback

def render_alert_card(rank, tract, alert_text):
    geoid  = tract["tract_geoid"]
    hi     = tract.get("heat_index_c")
    hi_str = f"{hi:.1f}°C" if hi else "N/A"
    label  = TRACT_LABELS.get(geoid, f"Tract {geoid[-6:]}")
    st.markdown(f"""
    <div class="alert-card">
        <span class="sim-badge">🔴 SIMULATED — NOT SENT</span>
        <h4>🚨 #{rank} · {label} &nbsp;|&nbsp; Risk: {tract['risk_score_final']:.3f} &nbsp;|&nbsp; HI Peak: {hi_str}</h4>
        <p>{alert_text}</p>
    </div>""", unsafe_allow_html=True)

# P1-6: Auto-load alert for #1 on page load
if top10:
    top_tract = top10[0]
    top_label = TRACT_LABELS.get(top_tract["tract_geoid"], "Top Tract")
    st.markdown(f"#### 📌 #{1} — {top_label} (highest risk, auto-generated)")
    with st.spinner("Generating Gemini alert for highest-risk tract..."):
        auto_alert = generate_gemini_alert(top_tract)
    render_alert_card(1, top_tract, auto_alert)

st.markdown("##### Generate alerts for additional tracts:")
opt_labels = [
    f"#{i+1} · {TRACT_LABELS.get(t['tract_geoid'], t['tract_geoid'][-6:])} (risk={t['risk_score_final']:.3f})"
    for i, t in enumerate(top10)
]
selected = st.multiselect(
    "Select tracts:",
    options=opt_labels,
    default=[],
    max_selections=4,
    help="Up to 4 more tracts. Gemini API with static fallback."
)
if selected and st.button("🔔 Generate Selected Alerts", type="primary"):
    for sel in selected:
        rank  = int(sel.split("·")[0].strip().replace("#", "")) - 1
        tract = top10[rank]
        with st.spinner(f"Generating alert for {TRACT_LABELS.get(tract['tract_geoid'], '')}..."):
            alert_text = generate_gemini_alert(tract)
        render_alert_card(rank + 1, tract, alert_text)

# ── Data Table ────────────────────────────────────────────────────────────────
with st.expander("📋 Full Top-10 Data Table", expanded=False):
    import pandas as pd
    rows = []
    for i, t in enumerate(top10):
        hi = t.get("heat_index_c")
        rows.append({
            "Rank": i + 1,
            "Neighborhood":   TRACT_LABELS.get(t["tract_geoid"], "—"),
            "GEOID":          t["tract_geoid"],
            "Risk Score":     round(t.get("risk_score_final", 0), 3),
            "Avg Temp °C":    round(t.get("mean_temp_c", 0), 1),
            "HI Peak °C":     round(hi, 1) if hi else None,
            "Vuln Index":     round(t.get("vulnerability_index", 0), 3),
            "Elderly %":      t.get("pct_age_65_proxy"),
            "Uninsured %":    t.get("pct_poverty_proxy"),
            "Utility Risk %": t.get("pct_no_ac_proxy"),
            "Population":     t.get("total_population"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#4a5568;font-size:0.78rem;padding:0.8rem 0">
    ⚠️ <b>Disclaimer:</b> Demonstration system using historical data (July 15, 2024).
    Not for operational emergency management use. &nbsp;|&nbsp;
    Data: FortyGuard API · CDC PLACES 2022 · US Census TIGER/Line &nbsp;|&nbsp;
    Built with Streamlit · Folium · Gemini 3.5 Flash Lite
</div>
""", unsafe_allow_html=True)