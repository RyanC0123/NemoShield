import streamlit as st
from api_client import APIError, api_get, api_post
from ui import inject_css, go, nemoshield_heading

inject_css()

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.write("")
    st.write("")
    nemoshield_heading()
    st.markdown("#### Autonomous cybersecurity, powered by Nemotron")
    st.caption("Detect → Investigate → Decide → Respond → Verify → Report")
    st.write("")

    with st.container(border=True):
        st.subheader("System check")
        backend_col, ai_col, device_col = st.columns(3)

        with backend_col:
            st.markdown("**Backend (FastAPI)**")
            try:
                backend = api_get("/health")
            except APIError as exc:
                st.error(str(exc))
            else:
                st.success(f"{backend['status'].title()} · v{backend['version']}")

        with ai_col:
            st.markdown("**Nemotron AI**")
            try:
                agent = api_get("/api/agent/status")
            except APIError as exc:
                st.error(str(exc))
            else:
                if agent["mode"] == "mock":
                    st.info("Mock analysis enabled")
                elif agent["configured"]:
                    st.success("API key configured")
                    if agent["test_available"]:
                        if st.button("Test live Nemotron connection"):
                            try:
                                result = api_post("/api/agent/test")
                            except APIError as exc:
                                st.error(f"Nemotron test failed: {exc}")
                            else:
                                st.session_state["nemotron_test_result"] = result
                        test_result = st.session_state.get("nemotron_test_result")
                        if test_result:
                            st.success(
                                f"Live model responded in "
                                f"{test_result['latency_ms']} ms."
                            )
                else:
                    st.warning("NVIDIA_API_KEY is not configured")
                st.caption("Model connectivity is checked when analysis runs.")

        with device_col:
            st.markdown("**Arduino device**")
            try:
                hardware = api_get("/hardware/status")
            except APIError as exc:
                st.error(str(exc))
            else:
                if hardware["connected"]:
                    st.success(f"Connected · {hardware['state']}")
                elif hardware["simulated"]:
                    st.info("Simulation mode · no board connected")
                else:
                    st.warning("Not connected")

    st.write("")
    if st.button("Start monitoring", type="primary", use_container_width=True):
        go("Pages/Dashboard.py")
