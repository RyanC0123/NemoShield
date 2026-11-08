import streamlit as st
from ui import inject_css, go, PLACEHOLDER

inject_css()

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.write("")
    st.write("")
    st.markdown("# 🛡️ NemoShield")
    st.markdown("#### Autonomous cybersecurity, powered by Nemotron")
    st.caption("Detect → Investigate → Decide → Respond → Verify → Report")
    st.write("")

    with st.container(border=True):
        st.subheader("System check")
        st.markdown(f"- Backend (FastAPI): {PLACEHOLDER}")
        st.markdown(f"- Nemotron API: {PLACEHOLDER}")
        st.markdown(f"- Arduino device: {PLACEHOLDER}")

    st.write("")
    if st.button("Start monitoring", type="primary", use_container_width=True):
        go("Pages/Dashboard.py")
