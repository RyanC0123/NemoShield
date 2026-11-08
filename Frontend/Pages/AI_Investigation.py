import streamlit as st

from api_client import APIError, api_get, api_post
from ui import inject_css, render_section_links

inject_css()
sections = {
    "reasoning": "Nemotron reasoning",
    "tools": "Tool calls",
    "evidence": "Evidence",
    "decisions": "Decisions",
}
selected = st.query_params.get("section", "reasoning")
selected = selected if selected in sections else "reasoning"

st.title("AI Investigation")
render_section_links("ai-investigation", selected, sections)

try:
    agent_status = api_get("/api/agent/status")
    event_response = api_get("/api/events", params={"limit": 100})
except APIError as exc:
    st.error(f"Could not load investigation data from the backend: {exc}")
    st.stop()

if agent_status["mode"] == "mock":
    st.info("Backend is using deterministic mock AI analysis.")
elif agent_status["configured"]:
    st.success("Nemotron API key is configured; analysis runs only when requested.")
else:
    st.warning("NVIDIA_API_KEY is not configured in the backend.")

events = event_response["events"]
if not events:
    st.info("The backend has no events to investigate.")
    st.stop()

event_by_id = {event["event_id"]: event for event in events}
event_id = st.selectbox(
    "Security event",
    list(event_by_id),
    format_func=lambda value: (
        f"{value} · {event_by_id[value]['event_type'].replace('_', ' ').title()} · "
        f"{event_by_id[value]['severity'].title()}"
    ),
    key="investigation_event_id",
)
event = event_by_id[event_id]
try:
    trace_response = api_get(
        "/api/traces",
        params={"event_id": event_id},
    )
except APIError as exc:
    st.error(f"Could not load persisted investigation history: {exc}")
    st.stop()

analysis_results = st.session_state.setdefault("nemoshield_ai_results", {})
decision_results = st.session_state.setdefault("nemoshield_decisions", {})

if selected == "reasoning":
    st.caption("Analyze the selected event through the backend's Nemotron service.")
    if agent_status["test_available"] and st.button(
        "Test live Nemotron connection",
        key="test_nemotron_from_investigation",
    ):
        try:
            result = api_post("/api/agent/test")
        except APIError as exc:
            st.error(f"Nemotron connection test failed: {exc}")
        else:
            st.success(
                f"Nemotron responded in {result['latency_ms']} ms."
            )
    if st.button("Run Nemotron analysis", type="primary"):
        try:
            response = api_post("/api/analyze", {"event_id": event_id})
        except APIError as exc:
            st.error(f"Nemotron analysis failed: {exc}")
        else:
            analysis_results[event_id] = response["analysis"]

    persisted_analysis = next(
        (
            trace["result"]
            for trace in trace_response["traces"]
            if trace["operation"] == "analyze"
            and trace["status"] == "completed"
            and isinstance(trace.get("result"), dict)
            and {
                "summary",
                "risk_level",
                "recommended_action",
            }.issubset(trace["result"])
        ),
        None,
    )
    analysis = analysis_results.get(event_id) or persisted_analysis
    if analysis:
        st.subheader("Analysis")
        st.write(analysis["summary"])
        col1, col2 = st.columns(2)
        col1.metric("Risk level", analysis["risk_level"].title())
        col2.write("**Recommended action**")
        col2.write(analysis["recommended_action"])
    else:
        st.info("Run analysis to request a result for this event.")
elif selected == "tools":
    st.caption("Persisted backend investigation traces for this event.")
    traces = trace_response["traces"]
    tool_calls = [
        {
            **call,
            "trace_id": trace["trace_id"],
            "operation": trace["operation"],
            "timestamp": trace["timestamp"],
        }
        for trace in traces
        for call in trace.get("tool_calls", [])
    ]
    if tool_calls:
        st.dataframe(tool_calls, hide_index=True, width="stretch")
    else:
        st.info(
            "No tool calls are recorded for this event. Mock-mode analyses "
            "use deterministic results; live Nemotron analyses record their "
            "read-only related-event lookup here."
        )
    for trace in traces:
        with st.expander(
            f"{trace['operation']} · {trace['status']} · {trace['timestamp']}"
        ):
            st.write(f"Trace ID: `{trace['trace_id']}`")
            st.write("Workflow steps")
            st.dataframe(trace["steps"], hide_index=True, width="stretch")
            if trace.get("error"):
                st.error(trace["error"])
elif selected == "evidence":
    st.caption("Raw event evidence returned by the backend.")
    st.json(event)
else:
    st.caption("Run analysis, record a decision, and update the Arduino alert.")
    if st.button("Run decision and Arduino alert", type="primary"):
        try:
            response = api_post(
                "/api/analyze-and-decide",
                {"event": event},
            )
        except APIError as exc:
            st.error(f"Decision pipeline failed: {exc}")
        else:
            decision_results[event_id] = response

    if st.button("Stop alert"):
        try:
            result = api_post(
                "/hardware/alert",
                {"level": "CLEAR", "reason": "Operator cleared Arduino alert"},
            )
        except APIError as exc:
            st.error(f"Could not clear the Arduino alert: {exc}")
        else:
            if result["ok"] and not result["simulated"]:
                st.success("Arduino alert cleared; board returned to NORMAL.")
            elif result["simulated"]:
                st.warning(
                    "The backend cleared the simulated alert, but no physical "
                    "Arduino was changed."
                )
            else:
                st.error(
                    f"The Arduino did not confirm CLEAR: "
                    f"{result.get('error', 'unknown hardware error')}"
                )

    try:
        decision_history = api_get(
            "/api/decisions",
            params={"event_id": event_id, "limit": 100},
        )
    except APIError as exc:
        st.error(f"Could not load decision history: {exc}")
        decision_history = {"decisions": []}

    result = decision_results.get(event_id)
    if result:
        st.subheader("Analysis")
        st.write(result["analysis"]["reason"])
        st.write(
            f"**Classification:** {result['analysis']['classification'].title()} · "
            f"**Risk score:** {result['analysis']['risk_score']}"
        )
        st.subheader("Decision")
        st.write(
            f"**Action:** {result['decision']['action'].replace('_', ' ').title()}"
        )
        st.write(f"**Response:** {result['decision']['response']['message']}")
        hardware = result["decision"]["response"].get("hardware")
        if hardware:
            if hardware["ok"] and not hardware["simulated"]:
                st.success(
                    f"Arduino acknowledged {hardware['command']} · "
                    f"state: {hardware['state']}"
                )
            elif hardware["simulated"]:
                st.warning(
                    f"Arduino command {hardware['command']} was simulated; "
                    "the physical board was not changed."
                )
            else:
                st.error(
                    f"Arduino command {hardware['command']} failed: "
                    f"{hardware.get('error') or 'no acknowledgment'}"
                )
        st.caption(
            f"Firewall response: {result['decision']['response']['status']} · "
            f"Firewall action executed: "
            f"{result['decision']['response']['executed']}"
        )
    else:
        if decision_history["decisions"]:
            result = decision_history["decisions"][0]
            st.subheader("Analysis")
            st.write(result["analysis"]["reason"])
            st.write(
                f"**Classification:** "
                f"{result['analysis']['classification'].title()} · "
                f"**Risk score:** {result['analysis']['risk_score']}"
            )
            st.subheader("Decision")
            st.write(
                f"**Action:** "
                f"{result['decision']['action'].replace('_', ' ').title()}"
            )
            st.write(f"**Response:** {result['decision']['response']['message']}")
            hardware = result["decision"]["response"].get("hardware")
            if hardware:
                status_message = (
                    "Physical board acknowledged"
                    if hardware["ok"] and not hardware["simulated"]
                    else "Board command was simulated"
                    if hardware["simulated"]
                    else f"Board command failed: {hardware.get('error')}"
                )
                st.write(
                    f"**Arduino:** {hardware['command']} · "
                    f"{hardware['state'] or status_message}"
                )
            st.caption(
                f"Decision ID: {result['decision_id']} · "
                f"{result['timestamp']}"
            )
        else:
            st.info("No decision history exists yet for this event.")
    if decision_history["decisions"]:
        with st.expander(
            f"Persistent decision history ({decision_history['total']})"
        ):
            st.dataframe(
                [
                    {
                        "Decision ID": item["decision_id"],
                        "Time": item["timestamp"],
                        "Classification": item["analysis"]["classification"],
                        "Action": item["decision"]["action"],
                        "Response": item["decision"]["response"]["status"],
                    }
                    for item in decision_history["decisions"]
                ],
                hide_index=True,
                width="stretch",
            )
