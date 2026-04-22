import streamlit as st
from sqlalchemy import text as _sql_text
from logic.cache_manager import clear_all_cache

def render_db_diagnostic(engine):
    """v6.4.0: Admin DB tanılama — TopBar göçü: sidebar yerine inline expander."""
    if (st.session_state.get('logged_in') and
            str(st.session_state.get('user_rol', '')).upper() == 'ADMIN'):
        with st.expander("🔧 DB Tanılama (Admin)", expanded=False):
            try:
                with engine.connect() as _conn:
                    _res = _conn.execute(_sql_text(
                        "SELECT current_schema(), current_database()"
                    )).fetchone()
                    st.caption(f"Schema: `{_res[0]}` | DB: `{_res[1]}`")
            except Exception as _diag_e:
                st.error(f"Tanılama hatası: {_diag_e}")

def render_admin_reset_button():
    """v6.2.0: Admin Cache/Session Reset — TopBar göçü: sidebar yerine inline."""
    if str(st.session_state.get('user_rol', '')).upper() == 'ADMIN':
        _, col_btn = st.columns([5, 1])
        with col_btn:
            if st.button("🧹 Reset (Admin)", width="stretch", key="admin_reset_btn"):
                clear_all_cache()
                st.session_state.clear()
                st.rerun()
