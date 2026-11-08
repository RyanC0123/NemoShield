"""Shared styling + helpers for NemoShield pages."""
import streamlit as st

PLACEHOLDER = "—"

TOP_NAV_CSS = """
<style>
  .st-key-nemoshield-navigation {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999999;
    height: 64px;
    padding: 0 20px;
    display: flex;
    align-items: center;
    background: rgba(8, 13, 23, 0.94);
    border-bottom: 1px solid rgba(148, 163, 184, 0.16);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    backdrop-filter: blur(18px);
  }
  .nemoshield-nav-link {
    color: inherit;
    text-decoration: none;
  }
  .st-key-nemoshield-navigation [data-testid="stHorizontalBlock"] {
    align-items: center;
    gap: 0.25rem;
    flex-wrap: nowrap;
    width: calc(100vw - 40px) !important;
    max-width: 1320px !important;
    margin: 0;
    display: grid !important;
    grid-template-columns: 150px 100px repeat(3, 150px) 140px 80px;
  }
  .st-key-nemoshield-navigation [data-testid="stColumn"] {
    min-width: 0 !important;
    flex: 1 1 0 !important;
    width: 0 !important;
  }
  .st-key-nemoshield-navigation button {
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    min-height: 38px !important;
    height: 38px !important;
    width: 100% !important;
    min-width: 0 !important;
    padding: 0 12px !important;
    border-radius: 8px !important;
    color: #cbd5e1 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    transition: color 150ms ease, background 150ms ease !important;
  }
  .st-key-nemoshield-navigation button:hover,
  .st-key-nemoshield-navigation button[aria-expanded="true"] {
    color: #fff !important;
    background: rgba(148, 163, 184, 0.10) !important;
  }
  .st-key-nemoshield-navigation button[kind="primary"] {
    color: #fff !important;
    background: rgba(59, 130, 246, 0.16) !important;
  }
  [data-testid="stPopoverBody"] button {
    width: 100%;
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    justify-content: flex-start;
    padding: 8px 10px !important;
    border-radius: 6px !important;
    color: inherit !important;
    text-align: left;
    font-weight: 500;
  }
  [data-testid="stPopoverBody"] button:hover {
    background: rgba(148, 163, 184, 0.10) !important;
  }
  .st-key-nemoshield-navigation [data-testid="stColumn"]:first-child button::before {
    content: "";
    width: 18px;
    height: 20px;
    margin-right: 8px;
    display: inline-block;
    flex: 0 0 auto;
    border: 2px solid #60a5fa;
    border-radius: 9px 9px 11px 11px;
    clip-path: polygon(50% 0, 100% 20%, 88% 78%, 50% 100%, 12% 78%, 0 20%);
  }
  .st-key-nemoshield-navigation [data-testid="stColumn"]:first-child button {
    color: #fff !important;
    font-size: 16px !important;
    font-weight: 750 !important;
    letter-spacing: -0.01em;
  }
  section[data-testid="stSidebar"],
  [data-testid="stSidebarCollapsedControl"] {
    display: none !important;
  }
  header[data-testid="stHeader"] {
    height: 0 !important;
  }
  .block-container {
    padding-top: 5.75rem !important;
  }
  .nemoshield-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999999;
    height: 64px;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0 18px;
    overflow: visible;
    background: rgba(8, 13, 23, 0.96);
    border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    backdrop-filter: blur(12px);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  .nemoshield-brand {
    box-sizing: border-box;
    height: 38px;
    display: inline-flex;
    align-items: center;
    flex: 0 0 auto;
    margin-right: 18px;
    padding: 0 11px;
    color: #f8fafc;
    font-size: 18px;
    font-weight: 700;
    text-decoration: none;
    white-space: nowrap;
  }
  .nemoshield-logo-mark {
    width: 18px;
    height: 21px;
    display: inline-block;
    margin-right: 8px;
    vertical-align: middle;
    border: 2px solid #60a5fa;
    border-radius: 9px 9px 11px 11px;
    clip-path: polygon(50% 0, 100% 20%, 88% 78%, 50% 100%, 12% 78%, 0 20%);
  }
  .nav-links {
    display: flex;
    align-items: center;
    gap: 3px;
    min-width: 0;
  }
  .nav-item {
    position: relative;
    flex: 0 0 auto;
  }
  .nav-item > a,
  .nav-trigger {
    box-sizing: border-box;
    height: 38px;
    min-height: 38px;
    display: inline-flex;
    align-items: center;
    padding: 0 11px;
    border-radius: 8px;
    color: #dbe4f0;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
  }
  .nav-item > a:hover,
  .nav-trigger:hover,
  .nav-item:focus-within > .nav-trigger {
    color: #fff;
    background: rgba(59, 130, 246, 0.16);
  }
  .nav-trigger::after {
    content: "";
    width: 6px;
    height: 6px;
    margin-left: 8px;
    border-right: 1.5px solid currentColor;
    border-bottom: 1.5px solid currentColor;
    transform: translateY(-2px) rotate(45deg);
  }
  .nav-menu {
    position: absolute;
    top: 44px;
    left: 0;
    min-width: 210px;
    display: none;
    visibility: hidden;
    opacity: 0;
    padding: 6px;
    background: #111827;
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 10px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.42);
    pointer-events: auto;
  }
  .nav-menu::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    top: -8px;
    height: 8px;
  }
  .nav-item:hover .nav-menu,
  .nav-item:focus-within .nav-menu {
    display: block;
    visibility: visible;
    opacity: 1;
  }
  .nav-menu a {
    display: block;
    box-sizing: border-box;
    width: 100%;
    padding: 8px 10px;
    border: 0;
    border-radius: 0;
    background: transparent;
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    appearance: none;
  }
  .nav-menu a:hover {
    color: white;
    background: rgba(148, 163, 184, 0.09);
  }
  .nav-item.active > a,
  .nav-item.active > .nav-trigger,
  .nemoshield-brand.active {
    color: #fff;
    font-weight: 700;
    background: rgba(59, 130, 246, 0.16);
  }
  @media (max-width: 900px) {
    .nemoshield-nav {
      overflow-x: auto;
    }
    .nav-links {
      overflow: visible;
    }
  }
</style>
"""

CSS = """
<style>
  .nemoshield-heading {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 0.5rem;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
  }
  .nemoshield-heading span {
    width: 26px;
    height: 30px;
    flex: 0 0 auto;
    border: 3px solid #60a5fa;
    border-radius: 13px 13px 16px 16px;
    clip-path: polygon(50% 0, 100% 20%, 88% 78%, 50% 100%, 12% 78%, 0 20%);
  }
  .muted { opacity:.65; font-size:0.9rem; }
  .pill { padding:4px 12px; border-radius:999px; font-size:0.8rem; }
  .pill-demo { background:rgba(128,128,128,.18); }
  .big { font-size:2rem; font-weight:700; line-height:1.1; }
  .dot { display:inline-block; width:56px; height:56px; border-radius:50%;
         opacity:.25; border:2px dashed rgba(128,128,128,.6); }
  .banner { border-radius:12px; padding:14px 20px; font-weight:600;
            background:rgba(34,197,94,.12); color:#16a34a; border:1px solid rgba(34,197,94,.35); }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def render_section_links(page_key, selected_key, sections):
    columns = st.columns(len(sections))
    for column, (section_key, label) in zip(columns, sections.items()):
        button_type = "primary" if section_key == selected_key else "tertiary"
        if column.button(label, key=f"{page_key}_section_{section_key}", type=button_type):
            st.query_params["page"] = page_key
            st.query_params["section"] = section_key
            st.rerun()


def go(page_path: str):
    """Navigate to another page (path relative to App.py)."""
    page_by_path = {
        "Pages/Welcome.py": "welcome",
        "Pages/Dashboard.py": "dashboard",
        "Pages/Incidents.py": "incidents",
        "Pages/AI_Investigation.py": "ai-investigation",
        "Pages/Arduino_Monitor.py": "arduino-monitor",
        "Pages/Demo_Simulation.py": "demo",
        "Pages/Trends.py": "trends",
    }
    page_key = page_by_path.get(page_path)
    if page_key:
        st.query_params["page"] = page_key
        st.rerun()
    else:
        st.switch_page(page_path)


def placeholder_page(title: str, blurb: str):
    inject_css()
    st.title(title)
    st.caption(blurb)
    with st.container(border=True):
        st.write("Content for this page will go here.")


def nemoshield_heading():
    st.markdown(
        '<div class="nemoshield-heading"><span aria-hidden="true"></span>NemoShield</div>',
        unsafe_allow_html=True,
    )


def render_top_navigation(active_page="welcome"):
    inject_css()
    st.markdown(TOP_NAV_CSS, unsafe_allow_html=True)

    def nav_link(page_key, label, dropdown=None):
        active = " active" if active_page == page_key else ""
        href = f"/?page={page_key}"
        if dropdown:
            item_class = f"nav-item{active}"
            menu = "".join(
                f'<a href="/?page={page_key}&section={section}" target="_self">{label}</a>'
                for section, label in dropdown
            )
            return (
                f'<div class="{item_class}"><span class="nav-trigger">{label}</span>'
                f'<div class="nav-menu">{menu}</div></div>'
            )
        return f'<div class="nav-item{active}"><a href="{href}" target="_self">{label}</a></div>'

    navbar = (
        '<nav class="nemoshield-nav">'
        '<a class="nemoshield-brand active" href="/?page=welcome" target="_self">'
        '<span class="nemoshield-logo-mark" aria-hidden="true"></span>NemoShield</a>'
        '<div class="nav-links">'
        + nav_link("dashboard", "Dashboard")
        + nav_link("incidents", "Incidents", (
            ("list", "Incident list"),
            ("severity", "Severity filter"),
            ("details", "Incident details"),
        ))
        + nav_link("ai-investigation", "AI Investigation", (
            ("reasoning", "Nemotron reasoning"),
            ("tools", "Tool calls"),
            ("evidence", "Evidence"),
            ("decisions", "Decisions"),
        ))
        + nav_link("arduino-monitor", "Arduino Monitor", (
            ("led", "LED / buzzer status"),
            ("connection", "Device connection"),
            ("acknowledgments", "Button acknowledgments"),
        ))
        + nav_link("demo", "Demo")
        + nav_link("trends", "Trends")
        + "</div></nav>"
    )
    st.markdown(navbar, unsafe_allow_html=True)
