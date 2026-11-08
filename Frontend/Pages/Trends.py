from datetime import datetime, timedelta

import streamlit as st

from api_client import APIError, api_get
from ui import go, inject_css

inject_css()
metric_names = ("Events", "Threats", "Blocked", "Critical")
current_metric = st.session_state.get("trend_metric", "Events")
if current_metric not in metric_names:
    current_metric = "Events"

metric = st.selectbox(
    "Metric",
    metric_names,
    index=metric_names.index(current_metric),
    key="trend_metric_select",
)
st.title(f"Recent {metric.lower()}")
st.caption("Counts are calculated from backend events and this session's decisions.")

range_label = st.segmented_control(
    "Range",
    ["1h", "24h", "7d"],
    default="24h",
    key="trend_range",
)

try:
    event_response = api_get("/api/events", params={"limit": 100})
    decision_response = api_get("/api/decisions", params={"limit": 100})
except APIError as exc:
    st.error(f"Could not load trend data from the backend: {exc}")
    st.stop()

events = event_response["events"]
decisions = decision_response["decisions"]

def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


if metric == "Blocked":
    data_points = [
        {
            "timestamp": result["timestamp"],
            "matches": True,
        }
        for result in decisions
        if result["decision"]["action"] == "simulated_block"
    ]
else:
    data_points = []
    for event in events:
        severity = event["severity"]
        matches = (
            metric == "Events"
            or metric == "Threats" and severity in ("high", "critical")
            or metric == "Critical" and severity == "critical"
        )
        if matches:
            data_points.append(
                {"timestamp": event["timestamp"], "matches": True}
            )

if not data_points:
    st.info(
        "No data points are available for this metric and session yet."
        if metric == "Blocked"
        else "The backend returned no matching events."
    )
else:
    timestamps = [parse_timestamp(point["timestamp"]) for point in data_points]
    latest = max(timestamps)
    if range_label == "1h":
        bucket_count, bucket_size = 12, timedelta(minutes=5)
    elif range_label == "7d":
        bucket_count, bucket_size = 7, timedelta(days=1)
    else:
        bucket_count, bucket_size = 24, timedelta(hours=1)
    end = latest + timedelta(microseconds=1)
    start = end - bucket_size * bucket_count

    chart_data = []
    for bucket_index in range(bucket_count):
        bucket_start = start + bucket_size * bucket_index
        bucket_end = bucket_start + bucket_size
        count = sum(
            bucket_start <= timestamp < bucket_end
            for timestamp in timestamps
        )
        chart_data.append({"Time": bucket_end, "Count": count})

    with st.container(border=True):
        st.line_chart(chart_data, x="Time", y="Count")
        st.caption(
            f"{len(data_points)} matching record(s), grouped relative to "
            f"the latest record at {latest:%Y-%m-%d %H:%M UTC}."
        )

if st.button("← Back to Dashboard"):
    go("Pages/Dashboard.py")
