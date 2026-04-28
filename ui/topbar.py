"""
ui/topbar.py — EKLERİSTAN QMS TopBar Navigasyon Sistemi
v1.0.0: Sidebar'sız, tek-kaynak navigasyon.

PRENSIP: Modül değişimi YALNIZCA bu dosyadaki butonlardan tetiklenir.
         Hiçbir modül-içi widget (selectbox, radio, form) modül değiştiremez.
         st.button → explicit kullanıcı aksiyonu → rerun (state kirliği yok).
"""
import streamlit as st
from static.logo_b64 import LOGO_B64
from logic.app_auth_flow import guvenli_cikis_yap
from logic.auth_logic import oturum_modul_guncelle
from logic.app_bootstrap import get_cookie_manager

# ─── CSS ───────────────────────────────────────────────────────────────────────
_TOPBAR_CSS = """
<style>
/* ── Sidebar ve toggle'ı tamamen kaldır ── */
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* ── Ana içerik tam genişliğe yay ── */
.main .block-container {
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}

/* ── Pasif navigasyon butonları (secondary) ── */
div.stButton > button[data-testid="stBaseButton-secondary"] {
    background-color: #1e293b !important;
    color: #cbd5e1 !important;
    border: 1px solid #334155 !important;
}

/* ── Tüm nav butonlarında esnek yükseklik ve metin kaydırma ── */
div.stButton > button {
    white-space: normal !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 0.8rem !important;
    min-height: 3.2rem !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}

/* ── Mobil uyum ── */
@media (max-width: 640px) {
    .main .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
}
</style>
"""

_NAV_PER_ROW = 9

from datetime import date as _date


def _sync_db(engine, slug):
    try:
        token = get_cookie_manager().get("qms_remember_me")
        if token:
            oturum_modul_guncelle(engine, token, slug)
    except Exception:
        pass


def render_topbar(modul_pairs, active_slug, engine):
    """v1.2.0: Kurumsal ergonomik header panel + esnek navigasyon."""
    st.markdown(_TOPBAR_CSS, unsafe_allow_html=True)

    aktif_lbl  = next((lbl for lbl, s in modul_pairs if s == active_slug), "Portal")
    u_fullname = st.session_state.get("user_fullname", "Misafir").title()
    u_rol      = st.session_state.get("user_rol", "")
    bugun      = _date.today().strftime("%d.%m.%Y")

    # ── Kurumsal Header Paneli ────────────────────────────────────────────
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.image(LOGO_B64, width=200)
        st.markdown(
            "<div style='padding-top:10px; text-align:left;'>"
            "<div style='font-size:1.8rem; font-weight:800; "
            "background:linear-gradient(90deg,#e11d48,#f97316); "
            "-webkit-background-clip:text; -webkit-text-fill-color:transparent; "
            "line-height:1.2;'>EKLERİSTAN QMS</div>"
            "<div style='font-size:1.0rem; color:#64748b; margin-top:2px; "
            "letter-spacing:0.05em;'>KALİTE YÖNETİM SİSTEMİ</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    with c_right:
        st.markdown(
            f"<div style='padding-top:30px; text-align:right;'>"
            f"<div style='font-size:1.4rem; font-weight:700; color:#f1f5f9;'>"
            f"👤 {u_fullname}</div>"
            f"<div style='font-size:1.0rem; color:#f97316; font-weight:600; margin-top:5px;'>"
            f"{u_rol}</div>"
            f"<div style='font-size:0.92rem; color:#94a3b8; margin-top:3px;'>"
            f"📍 {aktif_lbl} &nbsp;·&nbsp; 📅 {bugun}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Modül Navigasyon Butonları ────────────────────────────────────────
    n = len(modul_pairs)
    if n == 0:
        return

    rows = [modul_pairs[i: i + _NAV_PER_ROW] for i in range(0, n, _NAV_PER_ROW)]
    for row in rows:
        cols = st.columns(len(row))
        for idx, (lbl, slug) in enumerate(row):
            btn_type = "primary" if slug == active_slug else "secondary"
            if cols[idx].button(lbl, key=f"topnav_{slug}", type=btn_type, width="stretch"):
                if slug != active_slug:
                    st.session_state.active_module_key = slug
                    _sync_db(engine, slug)
                    st.rerun()

    st.divider()
