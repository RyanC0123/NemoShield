import streamlit as st

from api_client import APIError, api_get, api_post
from ui import inject_css, render_section_links

inject_css()
sections = {
    "led": "LED / buzzer status",
    "connection": "Device connection",
    "acknowledgments": "Button acknowledgments",
}
selected = st.query_params.get("section", "led")
selected = selected if selected in sections else "led"

st.title("Arduino Monitor")
render_section_links("arduino-monitor", selected, sections)

if st.button("Refresh device status"):
    st.rerun()

try:
    hardware = api_get("/hardware/status")
except APIError as exc:
    st.error(f"Could not read Arduino status from the backend: {exc}")
    st.stop()

if selected == "led":
    st.caption("Current device output state reported by the backend.")
    if hardware["connected"]:
        st.success(f"Board connected · alert state: {hardware['state']}")
    elif hardware["simulated"]:
        st.info(f"Simulation mode · alert state: {hardware['state']}")
    else:
        st.warning("No Arduino board is connected.")
    st.caption(
        "Clear an active alert here to stop the buzzer and return the LEDs to green."
    )
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
elif selected == "connection":
    st.caption("Connection information reported by the backend.")
    connection_col, mode_col, port_col = st.columns(3)
    connection_col.metric(
        "Connection",
        "Connected" if hardware["connected"] else "Disconnected",
    )
    mode_col.metric(
        "Mode",
        "Simulation" if hardware["simulated"] else "Hardware",
    )
    port_col.metric(
        "Port",
        hardware.get("port")
        or hardware.get("requested_port")
        or "Not detected",
    )
    st.write(f"**Baud rate:** {hardware['baud']}")
    available_ports = hardware.get("available_ports", [])
    if available_ports:
        st.write("**Serial ports detected by macOS:**")
        st.dataframe(
            available_ports,
            hide_index=True,
            width="stretch",
        )
    else:
        st.warning(
            "macOS currently reports no serial ports. Check that the Arduino "
            "is powered and connected with a data-capable USB cable."
        )
    if hardware["last_error"]:
        st.warning(f"Last device error: {hardware['last_error']}")
    st.caption(
        "Connect the Arduino, then use Reconnect and Ping to validate the "
        "serial connection. Ping does not change alert outputs."
    )
    if st.button("Reconnect Arduino"):
        try:
            hardware = api_post("/hardware/reconnect")
        except APIError as exc:
            st.error(f"Reconnect failed: {exc}")
        else:
            st.rerun()
    if st.button("Ping Arduino"):
        try:
            result = api_post("/hardware/ping")
        except APIError as exc:
            st.error(f"Device ping failed: {exc}")
        else:
            if result["ok"]:
                st.success(
                    "Device responded"
                    if not result["simulated"]
                    else "Backend ping succeeded in simulation mode"
                )
            else:
                st.warning("Device did not respond to the ping.")
else:
    st.caption("Button acknowledgments reported by the backend.")
    try:
        acknowledgments = api_get("/hardware/button-acks")
    except APIError as exc:
        st.error(f"Could not load button acknowledgments: {exc}")
    else:
        if acknowledgments:
            st.dataframe(acknowledgments, hide_index=True, width="stretch")
        else:
            st.info("No button acknowledgments have been recorded.")
