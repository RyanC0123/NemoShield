"""NemoShield - entry point. Run: streamlit run App.py"""
import streamlit as st

st.set_page_config(page_title="NemoShield", page_icon="🛡️", layout="wide")

pages = [
    st.Page("Pages/Welcome.py", title="Welcome", icon="👋", default=True),
    st.Page("Pages/Dashboard.py", title="Dashboard", icon="📊"),
    st.Page("Pages/Incidents.py", title="Incidents", icon="🚨"),
    st.Page("Pages/AI_Investigation.py", title="AI Investigation", icon="🧠"),
    st.Page("Pages/Arduino_Monitor.py", title="Arduino Monitor", icon="🔌"),
    st.Page("Pages/Demo_Simulation.py", title="Demo / Simulation", icon="🎯"),
    st.Page("Pages/Trends.py", title="Trends", icon="📈"),
]

with st.sidebar:
    st.markdown("### 🛡️ NemoShield")
    st.caption("Nemotron AI Cybersecurity Agent")

st.navigation(pages).run()
