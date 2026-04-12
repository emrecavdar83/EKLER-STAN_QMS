import streamlit as st
# Importlar ihtiyaç anında yapılacak (Döngüsel Bağımlılığı Kırmak İçin)

# --- 13. ADAM: CACHE TTL STANDARTLARI (Anayasa Md. 13) ---
CACHE_TTL = {
    'critical': 30,    # Yetki, personel, login (Hızlı yenilenme)
    'frequent': 60,    # Ürün, departman listesi
    'stable': 300,     # Ayarlar, modüller, statik veriler (5 dk)
    'static': 3600     # Nadir değişen büyük yapılar (1 saat)
}

def clear_query_cache():
    """Sadece genel sorgu cache'ini temizler — kayıt sonrası anlık güncelleme için."""
    from logic.data_fetcher import run_query, cached_veri_getir
    run_query.clear()
    cached_veri_getir.clear()

def clear_personnel_cache():
    """Personel ile ilgili tüm cache'leri temizler."""
    from logic.data_fetcher import cached_veri_getir, get_personnel_hierarchy, get_user_roles, run_query
    cached_veri_getir.clear()
    get_personnel_hierarchy.clear()
    get_user_roles.clear()
    run_query.clear()
    if 'batch_yetki_map' in st.session_state:
        st.session_state.pop('batch_yetki_map')
    st.toast("Personel verileri yenilendi.", icon="👤")

def clear_department_cache():
    """Departman ile ilgili tüm cache'leri temizler."""
    from logic.data_fetcher import get_department_tree, get_department_options_hierarchical, cached_veri_getir, run_query
    get_department_tree.clear()
    get_department_options_hierarchical.clear()
    cached_veri_getir.clear()
    run_query.clear()
    st.toast("Departman yapısı güncellendi.", icon="📁")

def clear_all_cache():
    """Tüm cache'leri temizler. Sadece 'Sistemi Temizle' butonu kullanır."""
    st.cache_data.clear()
    st.cache_resource.clear()
    if 'batch_yetki_map' in st.session_state:
        st.session_state.pop('batch_yetki_map')
    # v4.0.0: Global Yetki Önbelleğini temizle
    from logic.zone_yetki import _YETKI_CACHE
    _YETKI_CACHE.clear()
    st.toast("Tüm sistem cache'i temizlendi.", icon="🧹")
