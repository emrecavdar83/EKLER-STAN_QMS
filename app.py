# Ekleristan QMS - V: 6.2.0 - Grand Unification Refactor (Anayasa v5.0)
import streamlit as st
# 1. MUST BE FIRST CALL (Anayasa v5.0)
st.set_page_config(
    page_title="Ekleristan QMS",
    page_icon="https://www.ekleristan.com/wp-content/uploads/2024/02/EKLERISTAN-02-150x150.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. RUNTIME BOOTSTRAP (Branding, CSS, DB Sync)
from logic.app_bootstrap import init_app_runtime
init_app_runtime()
from database.connection import get_engine
engine = get_engine()

# 3. MODULAR IMPORTS (AFTER BOOTSTRAP)
from logic.app_auth_flow import bootstrap_session, login_screen
from logic.app_admin_tools import render_db_diagnostic, render_admin_reset_button

# 4. SESSION BOOTSTRAP (QR, Logout, Cookie Persistence)
bootstrap_session(engine)

def main_app():
    """v6.2.0: Orchestrates navigation and module dispatching"""
    from logic.zone_yetki import sorgu_sayisini_getir, _normalize_rol
    from ui.app_navigation import render_app_header, render_top_navigation, render_sidebar
    from ui.app_module_registry import render_module_dispatcher
    from logic.app_nav_sync import _modul_listesi_hazirla, _aktif_modulu_senkronize_et
    
    u_rol = _normalize_rol(st.session_state.get('user_rol', 'MISAFIR'))
    
    modul_pairs, modul_listesi, lbl_to_slug, slug_to_lbl = _modul_listesi_hazirla(u_rol)
    active_slug, selected_label, active_index = _aktif_modulu_senkronize_et(modul_pairs, modul_listesi, lbl_to_slug, slug_to_lbl)
    
    st.session_state.available_modules = modul_pairs
    
    render_app_header()
    render_top_navigation(modul_listesi, active_index, selected_label, engine)
    render_sidebar(st.session_state.get('user', 'Misafir'), modul_listesi, active_index, engine)
    
    if u_rol == 'ADMIN':
        st.sidebar.caption(f"⚡ Sorgu: {sorgu_sayisini_getir()}")
    
    render_module_dispatcher(engine, active_slug)

if __name__ == "__main__":
    if st.session_state.get('logged_in'): 
        from logic.zone_yetki import _normalize_rol
        u_rol = _normalize_rol(st.session_state.get('user_rol'))
        # v6.8.5: Emergency Session Diagnostics for ADMIN
        if u_rol == 'ADMIN' and st.sidebar.toggle("🛠️ Session Trace"):
            st.sidebar.write({k: v for k, v in st.session_state.items() if k not in ['yetki_haritasi', 'available_modules']})
        main_app()
    else: 
        login_screen(engine)

    # Admin Maintenance
    render_db_diagnostic(engine)
    render_admin_reset_button()
