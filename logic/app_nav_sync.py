import streamlit as st
from logic.auth_logic import sistem_modullerini_getir
from logic.zone_yetki import modul_gorebilir_mi

def _modul_listesi_hazirla(u_rol):
    """Kullanıcının rolüne göre modül listesini ve dönüşüm sözlüklerini hazırlar."""
    raw_pairs = [("🏠 Portal (Ana Sayfa)", "portal")] + list(sistem_modullerini_getir())
    modul_pairs = [m for m in raw_pairs if m[1] == 'portal' or u_rol == 'ADMIN' or modul_gorebilir_mi(m[1])]
    if all(m[1] != "profilim" for m in modul_pairs):
        modul_pairs.append(("👤 Profilim", "profilim"))
    modul_listesi = [m[0] for m in modul_pairs]
    lbl_to_slug = {m[0]: m[1] for m in raw_pairs}
    lbl_to_slug["👤 Profilim"] = "profilim"
    slug_to_lbl = {v: k for k, v in lbl_to_slug.items()}
    return modul_pairs, modul_listesi, lbl_to_slug, slug_to_lbl

def _aktif_modulu_senkronize_et(modul_pairs, modul_listesi, lbl_to_slug, slug_to_lbl):
    """v9.0.0: TopBar navigasyon — saf validasyon, sıfır sidebar bağımlılığı.

    Modül değişimi YALNIZCA ui/topbar.py butonlarından tetiklenir.
    Bu fonksiyon yalnızca:
      1. Haritaları session_state'e yazar (uyumluluk).
      2. active_module_key'i doğrular, yetkisizse portal'a düşürür.
      3. Etiket ve indeks hesaplar (topbar için gerekli).
    Sidebar_nav okuma tamamen kaldırıldı.
    """
    # Uyumluluk için haritayı session state'e yaz
    st.session_state['_lbl_to_slug_map'] = lbl_to_slug

    active_slug = st.session_state.get('active_module_key', 'portal')

    # Geçerlilik kontrolü — yetki dışı veya bilinmeyen slug varsa portal
    if not any(m[1] == active_slug for m in modul_pairs):
        active_slug = 'portal'
        st.session_state.active_module_key = 'portal'

    # Slug → label → index (portal fallback)
    selected_lbl = slug_to_lbl.get(active_slug)
    if not selected_lbl or selected_lbl not in modul_listesi:
        selected_lbl = modul_listesi[0]

    active_index = modul_listesi.index(selected_lbl)
    return active_slug, selected_lbl, active_index
