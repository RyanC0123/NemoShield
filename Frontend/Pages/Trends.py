import streamlit as st
from ui import inject_css, go

inject_css()

metric = st.session_state.get("trend_metric", "Events")
st.title(f"Recent {metric.lower()}")
st.caption("Trend over time.")

st.segmented_control(
    "Range", ["1h", "24h", "7d"], default="24h", key="trend_range"
)
with st.container(border=True, height=360):
    st.write("Trend graph will appear here.")

if st.button("← Back to Dashboard"):
    go("Pages/Dashboard.py")
