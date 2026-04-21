import streamlit as st
from logic.branding import render_corporate_header as _render_header
from logic.app_auth_flow import guvenli_cikis_yap
from logic.app_bootstrap import get_cookie_manager
from logic.auth_logic import oturum_modul_guncelle
from static.logo_b64 import LOGO_B64

def render_app_header():
    """v4.1.0: Premium Corporate Header"""
    _render_header()

def render_module_info(label):
    """v6.1.9: Renders current module indicator bar"""
    st.markdown(f"""
        <div style="text-align: center; color: #64748b; font-size: 0.9rem; padding-top: 5px;">
            <span style="font-weight: 600;">Modül:</span> {label}
        </div>
    """, unsafe_allow_html=True)

def render_sidebar(user, modul_listesi, active_index, engine):
    """v6.1.9: Sidebar navigation with user profile and logout"""
    with st.sidebar:
        st.image(LOGO_B64)
        st.write(f"👤 **{user}**")
        if st.button("🚪 Sistemi Kapat (Logout)", width="stretch", key="logout_btn"):
            guvenli_cikis_yap(engine)
        st.markdown("---")
        
        def sync_from_sidebar():
            try:
                label = st.session_state.get('sidebar_nav')
                from logic.auth_logic import MODUL_ESLEME
                # v6.1.9: Label-to-Slug mapping (needs to be consistent)
                # This will be refined in Phase 4 (Registry)
                # For now, we assume global access or a mapping function
                pass 
            except: pass

        st.radio("🏠 ANA MENÜ", modul_listesi, index=active_index, key="sidebar_nav")

def render_top_navigation(modul_listesi, active_index, label, engine):
    """v6.1.9: Top navigation bar with home button, info bar, and quick access - MOBIL UYUMLU"""
    c1, mid, c2 = st.columns([1, 2, 1])
    with c1:
        # Mobil menü (hamburger)
        if st.button("☰", help="Menüyü Aç", key="mobile_menu_btn", width="stretch"):
            st.session_state._sidebar_open = not st.session_state.get('_sidebar_open', False)
            st.rerun()

        # Masaüstü: Ana Sayfa butonu
        if st.session_state.get('active_module_key', 'portal') != "portal":
            if st.button("🏠 Ana Sayfa", width="stretch", key="global_home_btn"):
                st.session_state.active_module_key = "portal"
                _sync_module_db(engine, "portal")
                st.rerun()
    with mid:
        render_module_info(label)
    with c2:
        c2_1, c2_2 = st.columns([3, 1])
        with c2_1:
            # v8.8.2: FIX - Prevent unintended module change when radio/widget changes
            # Store previous selection to detect REAL user interaction vs Streamlit rerun
            prev_selected = st.session_state.get('_quick_nav_prev_selected', None)
            selected = st.selectbox("🚀 HIZLI", modul_listesi, index=active_index, key="quick_nav", label_visibility="collapsed")

            # Only change module if this is a genuine selectbox change (not just rerun)
            # Compare with previous value to avoid spurious changes
            if selected != prev_selected and selected != (modul_listesi[active_index] if active_index < len(modul_listesi) else None):
                st.session_state.active_module_key = selected
                st.session_state._quick_nav_prev_selected = selected
                st.rerun()
            else:
                # Store current value for next comparison
                st.session_state._quick_nav_prev_selected = selected
        with c2_2:
            if st.button("🚪", help="Sistemden Güvenli Çıkış (Logout)", key="top_logout_btn", width="stretch"):
                guvenli_cikis_yap(engine)

def _sync_module_db(engine, slug):
    """v5.8.0: Updates last active module in DB for session persistence"""
    try:
        token = get_cookie_manager().get("qms_remember_me")
        if token:
            oturum_modul_guncelle(engine, token, slug)
    except: pass
