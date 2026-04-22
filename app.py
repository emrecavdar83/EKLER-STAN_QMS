# Ekleristan QMS - V: 6.3.0 - TopBar Navigasyon (Anayasa v5.0)
import streamlit as st
# 1. MUST BE FIRST CALL (Anayasa v5.0)
st.set_page_config(
    page_title="Ekleristan QMS",
    page_icon="https://www.ekleristan.com/wp-content/uploads/2024/02/EKLERISTAN-02-150x150.png",
    layout="wide",
    initial_sidebar_state="collapsed",  # v6.3.0: TopBar — sidebar baştan kapalı
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
    """v6.3.0: TopBar navigasyon sistemi — sidebar bağımlılığı sıfır."""
    from logic.zone_yetki import sorgu_sayisini_getir, _normalize_rol
    from ui.topbar import render_topbar
    from ui.app_module_registry import render_module_dispatcher
    from logic.app_nav_sync import _modul_listesi_hazirla, _aktif_modulu_senkronize_et

    u_rol = _normalize_rol(st.session_state.get('user_rol', 'MISAFIR'))

    modul_pairs, modul_listesi, lbl_to_slug, slug_to_lbl = _modul_listesi_hazirla(u_rol)
    active_slug, selected_label, active_index = _aktif_modulu_senkronize_et(
        modul_pairs, modul_listesi, lbl_to_slug, slug_to_lbl
    )

    st.session_state.available_modules = modul_pairs

    render_topbar(modul_pairs, active_slug, engine)

    if u_rol == 'ADMIN':
        st.caption(f"⚡ Sorgu Sayacı: {sorgu_sayisini_getir()}")

    render_module_dispatcher(engine, active_slug)

if __name__ == "__main__":
    if st.session_state.get('logged_in'):
        from logic.zone_yetki import _normalize_rol
        u_rol = _normalize_rol(st.session_state.get('user_rol'))
        main_app()
    else:
        login_screen(engine)

    # Admin Maintenance (inline, sidebar yok)
    render_db_diagnostic(engine)
    render_admin_reset_button()
