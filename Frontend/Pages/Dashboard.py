from datetime import datetime

import streamlit as st

from api_client import APIError, api_get, api_post
from ui import go, inject_css, nemoshield_heading


def _read_dashboard_data():
    try:
        return (
            api_get("/api/dashboard/summary"),
            api_get("/api/events", params={"limit": 100}),
            api_get("/api/alerts"),
            api_get("/hardware/status"),
        )
    except APIError as exc:
        st.error(f"Could not load live dashboard data: {exc}")
        return None


inject_css()
left, right = st.columns([4, 2])
with left:
    nemoshield_heading()
with right:
    live = st.toggle("Live updates", value=True, key="live")

    @st.fragment(run_every="5s" if live else None)
    def clock():
        st.caption(f"Last updated: {datetime.now():%H:%M:%S}")

    clock()

action_col, alerts_col, _ = st.columns([1.3, 1.3, 1.4])
with action_col:
    if st.button("Run demo attack", type="primary", width="stretch"):
        go("Pages/Demo_Simulation.py")
with alerts_col:
    if st.button("View open alerts", width="stretch"):
        go("Pages/Incidents.py")


@st.fragment(run_every="5s" if live else None)
def live_dashboard():
    dashboard_data = _read_dashboard_data()
    if dashboard_data is None:
        st.info("Start the FastAPI backend to load live events and metrics.")
        return

    summary, event_response, alert_response, hardware = dashboard_data
    all_events = event_response["events"]
    alerts = alert_response["alerts"]
    open_alerts = [
        alert for alert in alerts if alert["status"] == "open"
    ]
    severity_counts = summary["severity_counts"]
    event_by_id = {event["event_id"]: event for event in all_events}
    simulated_decisions = list(
        st.session_state.get("nemoshield_decisions", {}).values()
    )
    simulated_blocks = sum(
        item["decision"]["action"] == "simulated_block"
        for item in simulated_decisions
    )

    if open_alerts:
        most_urgent = open_alerts[0]
        st.markdown(
            f'<div class="banner" style="background:rgba(239,68,68,.12);'
            f'color:#dc2626;border:1px solid rgba(239,68,68,.35)">'
            f'{len(open_alerts)} open backend alert(s) · '
            f'Most urgent: {most_urgent["severity"].title()} · '
            f'{most_urgent["event_id"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="banner">All good · No open backend alerts</div>',
            unsafe_allow_html=True,
        )
    st.caption("Live metrics are read from the NemoShield backend API.")
    st.write("")

    metrics = (
        ("Events", summary["total_events"]),
        ("Open alerts", len(open_alerts)),
        ("Simulated blocks (this session)", simulated_blocks),
        ("Critical", severity_counts["critical"]),
    )
    for column, (label, value) in zip(st.columns(4), metrics):
        column.metric(label, value)

    st.write("")
    with st.container(border=True):
        st.subheader("Needs attention")
        if open_alerts:
            alert = open_alerts[0]
            event = event_by_id.get(alert["event_id"])
            st.write(f"**{alert['severity'].title()}** · {alert['message']}")
            if event:
                st.caption(
                    f"{event['event_type'].replace('_', ' ').title()} · "
                    f"{event['source_ip']} → {event['destination_ip']}"
                )
            if st.button(
                f"Acknowledge {alert['alert_id']}",
                key="acknowledge_dashboard_alert",
            ):
                try:
                    api_post(
                        f"/api/alerts/{alert['alert_id']}/acknowledge"
                    )
                except APIError as exc:
                    st.error(f"Could not acknowledge alert: {exc}")
                else:
                    st.success("Alert acknowledgment saved.")
                    st.rerun()
        else:
            st.success("The backend currently reports no open alerts.")
        if st.button("Open incident list →", key="open_incident"):
            go("Pages/Incidents.py")

    st.write("")
    with st.container(border=True):
        head, badge = st.columns([4, 1])
        head.subheader("Live security events")
        badge.markdown(
            '<span class="pill pill-demo">Backend dataset</span>',
            unsafe_allow_html=True,
        )
        recent_events = sorted(
            all_events,
            key=lambda event: event["timestamp"],
            reverse=True,
        )[:5]
        if recent_events:
            st.dataframe(
                [
                    {
                        "Time": event["timestamp"],
                        "Event": event["event_type"].replace("_", " ").title(),
                        "Severity": event["severity"].title(),
                        "Source": str(event["source_ip"]),
                        "Status": (
                            "Alert"
                            if event["severity"] in ("high", "critical")
                            else "Recorded"
                        ),
                    }
                    for event in recent_events
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("The backend event dataset is empty.")
        if st.button("View all incidents →", key="all_incidents"):
            go("Pages/Incidents.py")

    st.write("")
    agent_col, device_col = st.columns(2)
    with agent_col:
        with st.container(border=True):
            st.subheader("Nemotron agent")
            latest_decision = (
                simulated_decisions[-1] if simulated_decisions else None
            )
            if latest_decision:
                analysis = latest_decision["analysis"]
                st.write(
                    f"Latest analysis: **{analysis['classification'].title()}** · "
                    f"risk score {analysis['risk_score']}"
                )
                st.caption(analysis["reason"])
            else:
                st.write("No analysis has been run from this frontend session.")
            if st.button("Open AI Investigation →", key="open_ai"):
                go("Pages/AI_Investigation.py")

    with device_col:
        with st.container(border=True):
            st.subheader("Arduino status")
            if hardware["connected"]:
                st.success(f"Connected · {hardware['state']}")
            elif hardware["simulated"]:
                st.info("Simulation mode · no board connected")
            else:
                st.warning("Not connected")
            st.caption(
                f"Button acknowledgments: {hardware['button_ack_count']}"
            )
            if st.button("Open Arduino Monitor →", key="open_arduino"):
                go("Pages/Arduino_Monitor.py")

    st.write("")
    with st.container(border=True):
        st.subheader("Recent activity")
        if simulated_decisions:
            latest = simulated_decisions[-1]
            for step in (
                ("Detected", latest["event"]["event_id"]),
                ("Investigated", latest["analysis"]["reason"]),
                ("Decided", latest["decision"]["action"]),
                (
                    "Responded",
                    latest["decision"]["response"]["message"],
                ),
            ):
                st.markdown(f"- **{step[0]}** — {step[1]}")
        else:
            st.info(
                "Activity will appear here after running an analysis or "
                "simulated decision."
            )


live_dashboard()
