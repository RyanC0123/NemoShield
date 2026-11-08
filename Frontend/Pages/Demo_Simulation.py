import streamlit as st

from api_client import APIError, api_get, api_post
from ui import inject_css

inject_css()
st.title("Demo")
st.caption("Run the backend's analysis and simulated-response pipeline.")
st.warning(
    "This uses a seeded security event. It does not generate attack traffic, "
    "change firewall rules, or actuate the Arduino."
)

try:
    event_response = api_get("/api/events", params={"limit": 100})
except APIError as exc:
    st.error(f"Could not load scenarios from the backend: {exc}")
    st.stop()

events = event_response["events"]
scenario_types = {
    "Port scan": "port_scan",
    "Brute-force login": "brute_force",
    "Suspicious login": "suspicious_login",
    "Normal traffic": "normal_traffic",
}
available_scenarios = [
    label for label, event_type in scenario_types.items()
    if any(event["event_type"] == event_type for event in events)
]

if not available_scenarios:
    st.info("The backend event dataset has no scenarios to run.")
    st.stop()

with st.container(border=True):
    st.subheader("Select a backend event")
    scenario = st.selectbox("Scenario type", available_scenarios)
    candidates = [
        event for event in events
        if event["event_type"] == scenario_types[scenario]
    ]
    event_by_id = {event["event_id"]: event for event in candidates}
    event_id = st.selectbox(
        "Event",
        list(event_by_id),
        format_func=lambda value: (
            f"{value} · {event_by_id[value]['severity'].title()} · "
            f"{event_by_id[value]['source_ip']}"
        ),
        key=f"demo_event_{scenario}",
    )
    event = event_by_id[event_id]
    st.caption(
        f"{event['timestamp']} · {event['source_ip']} → "
        f"{event['destination_ip']}"
    )
    if st.button("Run simulated defense workflow", type="primary"):
        try:
            result = api_post(
                "/api/analyze-and-decide",
                {"event": event},
            )
        except APIError as exc:
            st.error(f"Backend simulation failed: {exc}")
        else:
            st.session_state.setdefault("nemoshield_decisions", {})[
                event_id
            ] = result
            st.success("The backend completed and logged a simulated decision.")

result = st.session_state.get("nemoshield_decisions", {}).get(event_id)
with st.container(border=True):
    st.subheader("Workflow result")
    if result:
        analysis = result["analysis"]
        decision = result["decision"]
        response = decision["response"]
        st.markdown(f"1. **Detected** — {result['event']['event_id']}")
        st.markdown(
            f"2. **Investigated** — {analysis['classification'].title()} "
            f"(risk {analysis['risk_score']})"
        )
        st.markdown(f"3. **Decided** — {decision['action'].replace('_', ' ').title()}")
        st.markdown(f"4. **Responded** — {response['message']}")
        st.markdown(
            f"5. **Verified** — status `{response['status']}`, "
            f"executed `{response['executed']}`"
        )
        st.caption(
            f"Decision record: {result['decision_id']} · "
            f"{result['timestamp']}"
        )
    else:
        st.info("Select a scenario and run the workflow to see the backend result.")

st.caption("The backend stores a decision audit record; responses remain simulated.")
