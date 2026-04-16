# Ekleristan QMS - V: 6.2.0 - Grand Unification Refactor (Anayasa v5.0)
import streamlit as st
from logic.app_bootstrap import init_app_runtime
from logic.app_auth_flow import bootstrap_session, login_screen
from logic.app_admin_tools import render_db_diagnostic, render_admin_reset_button
from database.connection import get_engine

# 1. MUST BE FIRST CALL
st.set_page_config(
    page_title="Ekleristan QMS",
    page_icon="https://www.ekleristan.com/wp-content/uploads/2024/02/EKLERISTAN-02-150x150.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. RUNTIME BOOTSTRAP (Branding, CSS, DB Sync)
init_app_runtime()
engine = get_engine()

# 3. SESSION BOOTSTRAP (QR, Logout, Cookie Persistence)
bootstrap_session(engine)

def main_app():
    """v6.2.0: Orchestrates navigation and module dispatching"""
    from logic.auth_logic import sistem_modullerini_getir
    from logic.zone_yetki import modul_gorebilir_mi, sorgu_sayisini_getir
    from ui.app_navigation import render_app_header, render_top_navigation, render_sidebar
    from ui.app_module_registry import render_module_dispatcher
    u_rol = str(st.session_state.get('user_rol', 'MISAFIR')).upper()
    RAW_MODULE_PAIRS = [("🏠 Portal (Ana Sayfa)", "portal")] + list(sistem_modullerini_getir())
    # v6.2.1: Store (Label, Slug) pairs for robust Portal and Sidebar rendering
    modul_pairs = [m for m in RAW_MODULE_PAIRS if m[1] == 'portal' or u_rol == 'ADMIN' or modul_gorebilir_mi(m[1])]
    if all(m[1] != "profilim" for m in modul_pairs):
        modul_pairs.append(("👤 Profilim", "profilim"))
    
    modul_listesi = [m[0] for m in modul_pairs]
    st.session_state.available_modules = modul_pairs # Key Fix: Pass pairs to Portal
    
    LABEL_TO_SLUG = {m[0]: m[1] for m in RAW_MODULE_PAIRS}; LABEL_TO_SLUG["👤 Profilim"] = "profilim"
    SLUG_TO_LABEL = {v: k for k, v in LABEL_TO_SLUG.items()}
    active_slug = st.session_state.get('active_module_key', 'portal')
    
    # v6.2.5: Centralized Navigation Gatekeeper (Zırhlı Sürüm)
    # Track the last label we rendered to detect REAL user clicks on the radio/dropdown
    selected_label = SLUG_TO_LABEL.get(active_slug, modul_listesi[0])
    if 'prev_nav_label' not in st.session_state:
        st.session_state.prev_nav_label = selected_label

    new_slug = active_slug
    widget_label = st.session_state.get('sidebar_nav') or st.session_state.get('quick_nav')
    
    # Sync from widgets ONLY IF the user touched them (widget value differs from our tracked previous label)
    if widget_label and widget_label != st.session_state.prev_nav_label:
        tmp_slug = LABEL_TO_SLUG.get(widget_label)
        if tmp_slug and tmp_slug != active_slug:
            new_slug = tmp_slug
            st.session_state.active_module_key = new_slug
            st.session_state.prev_nav_label = widget_label # Update tracker
            st.rerun()
    
    # Update tracker if active_slug was changed from elsewhere (e.g. Portal)
    if active_slug != st.session_state.get('last_synced_slug'):
        st.session_state.prev_nav_label = selected_label
        st.session_state.last_synced_slug = active_slug

    active_index = modul_listesi.index(selected_label) if selected_label in modul_listesi else 0
    render_app_header()
    render_top_navigation(modul_listesi, active_index, selected_label, engine)
    from ui.app_navigation import render_sidebar
    render_sidebar(st.session_state.get('user', 'Misafir'), modul_listesi, active_index, engine)
    
    if st.session_state.get('user_rol') == 'ADMIN':
        st.sidebar.caption(f"⚡ Sorgu: {sorgu_sayisini_getir()}")
    
    render_module_dispatcher(engine, active_slug)

if __name__ == "__main__":
    if st.session_state.get('logged_in'): 
        main_app()
    else: 
        login_screen(engine)

# Admin Maintenance
render_db_diagnostic(engine)
render_admin_reset_button()
