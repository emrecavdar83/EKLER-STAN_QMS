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

/* ── Tüm nav butonlarında metin kırılmasını engelle ── */
div.stButton > button {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    font-size: 0.82rem !important;
    padding: 0.4rem 0.5rem !important;
    height: 2.6rem !important;
}

/* ── Ayarlar 16-tab yatay kaydırma ── */
.stTabs [data-baseweb="tab-list"] {
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
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
    """v1.1.0: Kurumsal header panel + navigasyon."""
    st.markdown(_TOPBAR_CSS, unsafe_allow_html=True)

    aktif_lbl  = next((lbl for lbl, s in modul_pairs if s == active_slug), "Portal")
    u_fullname = st.session_state.get("user_fullname", "Misafir").title()
    u_rol      = st.session_state.get("user_rol", "")
    bugun      = _date.today().strftime("%d.%m.%Y")

    # ── Kurumsal Header Paneli ────────────────────────────────────────────
    c_logo, c_brand, c_user, c_logout = st.columns([2, 5, 4, 1])

    with c_logo:
        st.image(LOGO_B64, width=150)

    with c_brand:
        st.markdown(
            "<div style='padding:12px 0 0 8px;'>"
            "<div style='font-size:1.6rem; font-weight:800; "
            "background:linear-gradient(90deg,#e11d48,#f97316); "
            "-webkit-background-clip:text; -webkit-text-fill-color:transparent; "
            "line-height:1.1;'>EKLERİSTAN QMS</div>"
            "<div style='font-size:0.8rem; color:#64748b; margin-top:4px; "
            "letter-spacing:0.05em;'>KALİTE YÖNETİM SİSTEMİ</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    with c_user:
        st.markdown(
            f"<div style='padding:10px 0 0 0; text-align:right;'>"
            f"<div style='font-size:1.1rem; font-weight:700; color:#f1f5f9;'>"
            f"👤 {u_fullname}</div>"
            f"<div style='font-size:0.82rem; color:#94a3b8; margin-top:3px;'>"
            f"<span style='color:#f97316;'>{u_rol}</span>"
            f"&nbsp;·&nbsp; 📍 {aktif_lbl}"
            f"&nbsp;·&nbsp; 📅 {bugun}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with c_logout:
        st.markdown("<div style='padding-top:22px;'>", unsafe_allow_html=True)
        if st.button("🚪", help="Güvenli Çıkış", key="topbar_logout", width="stretch"):
            guvenli_cikis_yap(engine)
        st.markdown("</div>", unsafe_allow_html=True)

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
