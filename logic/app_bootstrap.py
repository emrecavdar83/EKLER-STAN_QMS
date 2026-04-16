import streamlit as st
import extra_streamlit_components as cookie_manager
from logic.branding import set_branding
from database.connection import get_engine

def get_cookie_manager():
    """v5.8.1: Singleton Pattern using session_state to prevent DuplicateKeyError"""
    if "cookie_manager_instance" not in st.session_state:
        st.session_state.cookie_manager_instance = cookie_manager.CookieManager(key="qms_cookie_manager")
    return st.session_state.cookie_manager_instance

def init_app_runtime():
    """v6.1.9: Centralized runtime initialization (Branding, CSS, DB Sync)"""
    # 1. Force Schema Sync
    try:
        get_engine()
    except Exception as e:
        st.error(f"CRITICAL_MIGRATION_FAIL: {e}")
        st.session_state.migration_error = str(e)

    # 2. Branding (CSS Injection)
    set_branding()
    
    # 3. Global CSS Overrides
    st.markdown("""
    <style>
    div.stButton > button:first-child {background-color: #8B0000; color: white; width: 100%; border-radius: 5px;}
    .stRadio > label {font-weight: bold;}
    @media (min-width: 1024px) {
        [data-testid="stHeaderActionElements"], .stAppDeployButton, [data-testid="stManageAppButton"], 
        [data-testid="stDecoration"], footer { display: none !important; }
    }
    /* v4.7.1: Dropdown (Selectbox) Z-Index Zırhı */
    div[data-baseweb="popover"], div[role="listbox"] {
        z-index: 9999999 !important;
    }
    </style>
    """, unsafe_allow_html=True)
