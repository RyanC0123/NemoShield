"""Shared styling + helpers for NemoShield pages."""
import streamlit as st

PLACEHOLDER = "—"

CSS = """
<style>
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


def go(page_path: str):
    """Navigate to another page (path relative to App.py)."""
    st.switch_page(page_path)


def placeholder_page(title: str, blurb: str):
    inject_css()
    st.title(title)
    st.caption(blurb)
    with st.container(border=True):
        st.write("Content for this page will go here.")
