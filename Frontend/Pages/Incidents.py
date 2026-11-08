import streamlit as st

from api_client import APIError, api_get, api_post
from ui import inject_css, render_section_links

inject_css()
section_labels = {
    "list": "Incident list",
    "severity": "Severity filter",
    "details": "Incident details",
}
selected = st.query_params.get("section", "list")
selected = selected if selected in section_labels else "list"

st.title("Incidents")
render_section_links("incidents", selected, section_labels)

try:
    alert_response = api_get("/api/alerts")
    event_response = api_get("/api/events", params={"limit": 100})
except APIError as exc:
    st.error(f"Could not load incidents from the backend: {exc}")
    st.info("Check that the NemoShield API is running and try again.")
    st.stop()

alerts = alert_response["alerts"]
events_by_id = {
    event["event_id"]: event for event in event_response["events"]
}

if selected == "list":
    open_count = sum(alert["status"] == "open" for alert in alerts)
    st.caption(
        f"{open_count} open alert(s), {len(alerts) - open_count} acknowledged."
    )
    if alerts:
        rows = []
        for alert in alerts:
            event = events_by_id.get(alert["event_id"], {})
            rows.append(
                {
                    "Alert": alert["alert_id"],
                    "Event": alert["event_id"],
                    "Severity": alert["severity"].title(),
                    "Type": event.get("event_type", "Unknown").replace(
                        "_", " "
                    ).title(),
                    "Source": str(event.get("source_ip", "Unknown")),
                    "Status": alert["status"].title(),
                }
            )
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.success("The backend reports no open alerts.")
elif selected == "severity":
    st.caption("Filter backend alerts by severity.")
    severity = st.selectbox(
        "Severity",
        ["All", "Critical", "High", "Medium", "Low"],
    )
    filtered_alerts = [
        alert for alert in alerts
        if severity == "All" or alert["severity"] == severity.lower()
    ]
    st.write(f"{len(filtered_alerts)} matching alert(s)")
    if filtered_alerts:
        st.dataframe(
            [
                {
                    "Alert": alert["alert_id"],
                    "Event": alert["event_id"],
                    "Severity": alert["severity"].title(),
                    "Message": alert["message"],
                    "Status": alert["status"].title(),
                }
                for alert in filtered_alerts
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No alerts match this severity.")
else:
    st.caption("Inspect an alert and the security event that generated it.")
    if not alerts:
        st.info("The backend currently reports no open alerts.")
    else:
        alert_id = st.selectbox(
            "Alert",
            [alert["alert_id"] for alert in alerts],
            format_func=lambda value: next(
                f"{alert['alert_id']} · {alert['severity'].title()} · "
                f"{alert['event_id']}"
                for alert in alerts
                if alert["alert_id"] == value
            ),
        )
        alert = next(item for item in alerts if item["alert_id"] == alert_id)
        event = events_by_id.get(alert["event_id"])
        st.subheader(f"{alert['severity'].title()} alert")
        st.write(alert["message"])
        st.write(f"**Status:** {alert['status'].title()}")
        if event:
            st.json(event)
        else:
            st.warning("The event detail is not in the current event response.")
        if alert["status"] == "open" and st.button(
            "Acknowledge alert",
            type="primary",
        ):
            try:
                api_post(f"/api/alerts/{alert_id}/acknowledge")
            except APIError as exc:
                st.error(f"Could not acknowledge alert: {exc}")
            else:
                st.success("Acknowledgment saved.")
                st.rerun()

st.caption("Acknowledgments are persisted by the backend.")
