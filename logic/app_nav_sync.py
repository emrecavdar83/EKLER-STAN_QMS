import streamlit as st
from logic.auth_logic import sistem_modullerini_getir
from logic.zone_yetki import modul_gorebilir_mi

def _modul_listesi_hazirla(u_rol):
    """Kullanıcının rolüne göre modül listesini ve dönüşüm sözlüklerini hazırlar."""
    raw_pairs = [("🏠 Portal (Ana Sayfa)", "portal")] + list(sistem_modullerini_getir())
    
    # Sadece yetkili olunan modüller (v6.2.1)
    modul_pairs = [m for m in raw_pairs if m[1] == 'portal' or u_rol == 'ADMIN' or modul_gorebilir_mi(m[1])]
    
    if all(m[1] != "profilim" for m in modul_pairs):
        modul_pairs.append(("👤 Profilim", "profilim"))
    
    modul_listesi = [m[0] for m in modul_pairs]
    
    lbl_to_slug = {m[0]: m[1] for m in raw_pairs}
    lbl_to_slug["👤 Profilim"] = "profilim"
    slug_to_lbl = {v: k for k, v in lbl_to_slug.items()}
    
    return modul_pairs, modul_listesi, lbl_to_slug, slug_to_lbl

def _aktif_modulu_senkronize_et(modul_pairs, modul_listesi, lbl_to_slug, slug_to_lbl):
    """Widget'lardan gelen seçimleri ve active_module_key'i senkronize eder."""
    active_slug = st.session_state.get('active_module_key', 'portal')
    selected_lbl = slug_to_lbl.get(active_slug) or st.session_state.get('prev_nav_label', modul_listesi[0])
    
    if 'prev_nav_label' not in st.session_state:
        st.session_state.prev_nav_label = selected_lbl

    widget_lbl = st.session_state.get('sidebar_nav') or st.session_state.get('quick_nav')
    _widget_secimi_uygula(widget_lbl, active_slug, modul_pairs, lbl_to_slug)
    _kayip_slug_kurtar(active_slug, widget_lbl, modul_pairs, lbl_to_slug)
    
    if active_slug != st.session_state.get('last_synced_slug'):
        st.session_state.prev_nav_label = slug_to_lbl.get(active_slug, selected_lbl)
        st.session_state.last_synced_slug = active_slug

    active_index = modul_listesi.index(selected_lbl) if selected_lbl in modul_listesi else 0
    return active_slug, selected_lbl, active_index

def _widget_secimi_uygula(widget_lbl, active_slug, modul_pairs, lbl_to_slug):
    """Kullanıcı widget'tan seçim yaptısa state'e uygula."""
    if widget_lbl and widget_lbl != st.session_state.prev_nav_label:
        tmp_slug = lbl_to_slug.get(widget_lbl)
        if tmp_slug and tmp_slug != active_slug and any(m[1] == tmp_slug for m in modul_pairs):
            st.session_state.active_module_key = tmp_slug
            st.session_state.prev_nav_label = widget_lbl
            st.rerun()

def _kayip_slug_kurtar(active_slug, widget_lbl, modul_pairs, lbl_to_slug):
    """Zırhlı Recovery: Eğer active_slug portal ama widget başka modüldeyse kurtar."""
    if active_slug == "portal" and widget_lbl and widget_lbl in lbl_to_slug:
        recovered = lbl_to_slug[widget_lbl]
        if recovered != "portal" and any(m[1] == recovered for m in modul_pairs):
             st.session_state.active_module_key = recovered
             st.rerun()
