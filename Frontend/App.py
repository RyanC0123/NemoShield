"""NemoShield - entry point. Run: streamlit run App.py"""
import sys
from pathlib import Path

import streamlit as st

FRONTEND_DIR = str(Path(__file__).resolve().parent)
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

from ui import render_top_navigation

st.set_page_config(page_title="NemoShield", layout="wide")

pages = [
    st.Page("Pages/Welcome.py", title="Welcome", default=True),
    st.Page("Pages/Dashboard.py", title="Dashboard"),
    st.Page("Pages/Incidents.py", title="Incidents"),
    st.Page("Pages/AI_Investigation.py", title="AI Investigation"),
    st.Page("Pages/Arduino_Monitor.py", title="Arduino Monitor"),
    st.Page("Pages/Demo_Simulation.py", title="Demo"),
    st.Page("Pages/Trends.py", title="Trends"),
]

page_by_key = {
    "welcome": pages[0],
    "dashboard": pages[1],
    "incidents": pages[2],
    "ai-investigation": pages[3],
    "arduino-monitor": pages[4],
    "demo": pages[5],
    "trends": pages[6],
}

requested_page = st.query_params.get("page")
if requested_page:
    st.session_state["nemoshield_page"] = requested_page
requested_page = st.session_state.get("nemoshield_page", requested_page or "welcome")
render_top_navigation(requested_page)

selected_page = page_by_key.get(requested_page, pages[0])
st.navigation([selected_page], position="hidden").run()
