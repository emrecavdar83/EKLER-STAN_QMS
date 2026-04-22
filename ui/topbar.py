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
    background-color: #e2e8f0 !important;
    color: #334155 !important;
    border: 1px solid #cbd5e1 !important;
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

_NAV_PER_ROW = 8  # Satır başına max buton sayısı


def _sync_db(engine, slug):
    """DB'ye aktif modülü yaz (oturum kalıcılığı için)."""
    try:
        token = get_cookie_manager().get("qms_remember_me")
        if token:
            oturum_modul_guncelle(engine, token, slug)
    except Exception:
        pass


def render_topbar(modul_pairs, active_slug, engine):
    """
    v1.0.0: Sidebar'sız tam ekran TopBar navigasyon bileşeni.

    Args:
        modul_pairs : [(etiket, slug), ...] — rol bazlı filtrelenmiş liste
        active_slug : str — şu an aktif olan modülün slug'ı
        engine      : SQLAlchemy engine (DB sync için)
    """
    st.markdown(_TOPBAR_CSS, unsafe_allow_html=True)

    # ── Başlık Çubuğu: Logo | Aktif Modül + Kullanıcı | Çıkış ────────────
    aktif_lbl = next((lbl for lbl, s in modul_pairs if s == active_slug), "Portal")
    user = st.session_state.get("user", "Misafir")
    u_rol = st.session_state.get("user_rol", "")

    c_logo, c_info, c_logout = st.columns([1, 10, 1])
    with c_logo:
        st.image(LOGO_B64, width=55)
    with c_info:
        st.markdown(
            f"<div style='line-height:1.5; padding:2px 0;'>"
            f"<span style='color:#64748b; font-size:0.78rem;'>👤 {user} &nbsp;·&nbsp; {u_rol}</span><br>"
            f"<span style='color:#1e293b; font-weight:700; font-size:1.05rem;'>📍 {aktif_lbl}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c_logout:
        if st.button("🚪", help="Güvenli Çıkış (Logout)", key="topbar_logout", width="stretch"):
            guvenli_cikis_yap(engine)

    st.divider()

    # ── Modül Navigasyon Butonları ─────────────────────────────────────────
    n = len(modul_pairs)
    if n == 0:
        return

    rows = [modul_pairs[i: i + _NAV_PER_ROW] for i in range(0, n, _NAV_PER_ROW)]
    for row in rows:
        cols = st.columns(len(row))
        for idx, (lbl, slug) in enumerate(row):
            btn_type = "primary" if slug == active_slug else "secondary"
            if cols[idx].button(
                lbl, key=f"topnav_{slug}", type=btn_type, width="stretch"
            ):
                if slug != active_slug:
                    st.session_state.active_module_key = slug
                    _sync_db(engine, slug)
                    st.rerun()

    st.divider()
