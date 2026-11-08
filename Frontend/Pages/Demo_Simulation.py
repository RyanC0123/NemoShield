import streamlit as st
from ui import inject_css

inject_css()
st.title("Demo / Simulation")
st.caption("Trigger a test event and watch the full defense workflow.")

with st.container(border=True):
    st.subheader("Attack scenarios")
    st.selectbox(
        "Scenario",
        ["Port scan", "Brute-force login", "Other (placeholder)"],
        key="demo_scenario",
    )
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button("▶ Trigger security event", type="primary"):
        st.toast("Event triggered (placeholder)")
    if c2.button("↺ Reset demo"):
        st.toast("Demo reset (placeholder)")

with st.container(border=True):
    st.subheader("Workflow progress")
    st.caption("Detect → Investigate → Decide → Respond → Verify → Report")
    for step in ("Detect", "Investigate", "Decide", "Respond", "Verify", "Report"):
        st.markdown(f"◻️ **{step}** — —")
