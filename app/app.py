"""
app/app.py — HeatGuard Alerts Dashboard (Streamlit)
====================================================
Entry point for the Streamlit dashboard.
Run with: streamlit run app/app.py

STATUS: Scaffold only — populated incrementally per PRD milestones.
"""

import streamlit as st
import sys
from pathlib import Path

# Make sure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DEMO_CITY, DEMO_DATE

st.set_page_config(
    page_title="HeatGuard Alerts",
    page_icon="???",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("??? HeatGuard Alerts")
st.subheader("Vulnerability-Targeted Heat Early Warning System")
st.caption(f"Demo city: {DEMO_CITY or 'TBD'} | Snapshot date: {DEMO_DATE or 'TBD (locked after API validation)'}")

st.info(
    "**Status:** Project scaffold deployed. API validation in progress (Hour 0-2). "
    "Dashboard will populate after working city/date/AOI combo is confirmed.",
    icon="??"
)

with st.expander("About this project"):
    st.markdown("""
    HeatGuard Alerts fuses hyperlocal FortyGuard temperature data with CDC/Census vulnerability 
    data to identify the highest-risk census tracts during a heat event.
    
    **Components being built:**
    - ??? Choropleth risk map (heat + vulnerability overlay)
    - ?? Top-10 ranked risk list with score breakdown
    - ?? Simulated alert feed (Gemini-generated, plain-language)
    
    *All data is historical/simulated. No real alerts are sent.*
    """)

st.markdown("---")
st.caption("FortyGuard Hackathon '26 — Track 04: Government & Public Policy")
