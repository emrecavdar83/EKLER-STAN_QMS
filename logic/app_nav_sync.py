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
    """v8.9.2: Tek sorumluluk: active_module_key'den index hesapla.
    - Sidebar değişimlerini handle eder
    - quick_nav değişimlerini app_navigation.py handle eder
    - lbl_to_slug'ı session state'e yazar (app_navigation.py okuyabilsin)
    """
    # lbl_to_slug'ı session state'e kaydet (app_navigation.py ihtiyaç duyar)
    st.session_state['_lbl_to_slug_map'] = lbl_to_slug

    active_slug = st.session_state.get('active_module_key', 'portal')

    # Sidebar'dan navigasyon (quick_nav değil)
    sidebar_lbl = st.session_state.get('sidebar_nav')
    if sidebar_lbl and sidebar_lbl in lbl_to_slug:
        sidebar_slug = lbl_to_slug[sidebar_lbl]
        if sidebar_slug and sidebar_slug != active_slug and any(m[1] == sidebar_slug for m in modul_pairs):
            st.session_state.active_module_key = sidebar_slug
            st.rerun()
        active_slug = st.session_state.get('active_module_key', 'portal')

    # Active slug → label → index
    selected_lbl = slug_to_lbl.get(active_slug)
    if not selected_lbl or selected_lbl not in modul_listesi:
        selected_lbl = modul_listesi[0]
        # Eğer active_slug geçersizse portal'a sıfırla
        if active_slug != 'portal':
            st.session_state.active_module_key = 'portal'

    active_index = modul_listesi.index(selected_lbl)
    return active_slug, selected_lbl, active_index
