import streamlit as st
from sqlalchemy import text as _sql_text
from logic.cache_manager import clear_all_cache

def render_db_diagnostic(engine):
    """v6.3.9: Sidebar DB diagnostics for ADMIN users"""
    if (st.session_state.get('logged_in') and
            str(st.session_state.get('user_rol', '')).upper() == 'ADMIN'):
        if st.sidebar.checkbox("🔧 DB Tanılama (Admin)", key="db_diag_cb"):
            try:
                with engine.connect() as _conn:
                    _res = _conn.execute(_sql_text(
                        "SELECT current_schema(), current_database()"
                    )).fetchone()
                    st.sidebar.caption(f"Schema: `{_res[0]}` | DB: `{_res[1]}`")
            except Exception as _diag_e:
                st.sidebar.error(f"Tanılama hatası: {_diag_e}")

def render_admin_reset_button():
    """v6.1.0: Sidebar Cache/Session Reset for ADMIN users"""
    if str(st.session_state.get('user_rol', '')).upper() == 'ADMIN':
        if st.sidebar.button("🧹 Reset (Admin)", width="stretch", key="admin_reset_btn"):
            clear_all_cache()
            st.session_state.clear()
            st.rerun()
