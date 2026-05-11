"""
Clarivise — Streamlit Community Cloud entry point.
Serves the clarivise.html marketing website directly.
Portal pages (Request a key) remain as separate Streamlit pages.
"""
import streamlit as st
import os

st.set_page_config(
    page_title="Clarivise — AI-Powered Email Security",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide all Streamlit chrome for a clean website experience
st.markdown("""
<style>
    #MainMenu, header, footer { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stAppViewContainer"] { background: #060d1a; }
    [data-testid="stMain"] { padding: 0; }
</style>
""", unsafe_allow_html=True)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clarivise.html")

try:
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=7000, scrolling=True)
except FileNotFoundError:
    st.error("clarivise.html not found in repo root.")