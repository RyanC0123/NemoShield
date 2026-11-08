from datetime import datetime

import streamlit as st
from ui import inject_css, go, PLACEHOLDER

inject_css()

# ---------- Header + live clock ----------
left, right = st.columns([4, 2])
with left:
    st.title("🛡️ NemoShield")
with right:
    live = st.toggle("Live updates", value=True, key="live")

    @st.fragment(run_every="1s" if live else None)
    def clock():
        st.caption(f"Last updated: {datetime.now():%H:%M:%S}")

    clock()

# ---------- Status banner (swap text by state: All good / No incidents / ...) ----------
st.markdown('<div class="banner">All good · No incidents</div>', unsafe_allow_html=True)
st.write("")

# ---------- Quick actions ----------
qa1, qa2, _ = st.columns([1.3, 1.3, 1.4])
with qa1:
    if st.button("▶ Run demo attack", type="primary", use_container_width=True):
        go("Pages/Demo_Simulation.py")
with qa2:
    if st.button("✓ Acknowledge alert", use_container_width=True):
        st.toast("Alert acknowledged (placeholder)")

st.write("")

# ---------- Metrics, each with a "Recent ..." trend link ----------
METRICS = [
    ("Events", "Recent events"),
    ("Threats", "Recent threats"),
    ("Blocked", "Recent blocks"),
    ("Critical", "Recent critical"),
]
for col, (label, trend_label) in zip(st.columns(4), METRICS):
    with col:
        st.markdown(
            f'<div class="muted">{label}</div><div class="big">{PLACEHOLDER}</div>',
            unsafe_allow_html=True,
        )
        if st.button(f"{trend_label} ↗", key=f"trend_{label}", type="tertiary"):
            st.session_state["trend_metric"] = label
            go("Pages/Trends.py")

st.write("")

# ---------- Needs attention ----------
with st.container(border=True):
    st.subheader("Needs attention")
    st.caption("The incident to act on next will show here.")
    st.write(PLACEHOLDER)
    if st.button("Open incident →", key="open_incident"):
        go("Pages/Incidents.py")

st.write("")

# ---------- Live security events ----------
with st.container(border=True):
    h1, h2 = st.columns([4, 1])
    h1.subheader("Live security events")
    h2.markdown('<span class="pill pill-demo">Demo data</span>', unsafe_allow_html=True)
    t1, t2, t3 = st.columns(3)
    t1.markdown("**Event**")
    t2.markdown("**Severity**")
    t3.markdown("**Status**")
    for _ in range(3):
        r1, r2, r3 = st.columns(3)
        r1.write(PLACEHOLDER)
        r2.write(PLACEHOLDER)
        r3.write(PLACEHOLDER)
    if st.button("View all incidents →", key="all_incidents"):
        go("Pages/Incidents.py")

st.write("")

# ---------- Agent + Arduino ----------
a, b = st.columns(2)
with a:
    with st.container(border=True):
        st.subheader("🧠 Nemotron agent")
        st.write("Current task will appear here.")
        st.markdown("◻️ Log analysis")
        st.markdown("◻️ Threat evaluation")
        st.markdown("◻️ Decision")
        if st.button("Open AI Investigation →", key="open_ai"):
            go("Pages/AI_Investigation.py")
with b:
    with st.container(border=True):
        st.subheader("🔌 Arduino status")
        for col, label in zip(st.columns(3), ("Safe", "Warn", "Alert")):
            col.markdown(
                f'<div style="text-align:center"><span class="dot"></span>'
                f'<div class="muted">{label}</div></div>',
                unsafe_allow_html=True,
            )
        st.caption(f"LED indicators · Buzzer alerts · Connection: {PLACEHOLDER}")
        if st.button("Open Arduino Monitor →", key="open_arduino"):
            go("Pages/Arduino_Monitor.py")

st.write("")

# ---------- Recent activity timeline ----------
with st.container(border=True):
    st.subheader("Recent activity")
    st.caption("Each step the agent takes, newest first.")
    for step in ("Detected", "Investigated", "Decided", "Responded", "Verified"):
        st.markdown(f"◻️ **{step}** — {PLACEHOLDER}")
