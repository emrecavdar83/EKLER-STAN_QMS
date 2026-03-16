import streamlit as st
from logic.data_fetcher import (
    cached_veri_getir,
    get_personnel_hierarchy,
    get_user_roles,
    get_department_tree,
    get_department_options_hierarchical,
    run_query
)

def clear_personnel_cache():
    """Personel ile ilgili tüm cache'leri temizler."""
    cached_veri_getir.clear()
    get_personnel_hierarchy.clear()
    get_user_roles.clear()
    run_query.clear()
    st.toast("Personel verileri yenilendi.", icon="👤")

def clear_department_cache():
    """Departman ile ilgili tüm cache'leri temizler."""
    get_department_tree.clear()
    get_department_options_hierarchical.clear()
    cached_veri_getir.clear()
    run_query.clear()
    st.toast("Departman yapısı güncellendi.", icon="📁")

def clear_all_cache():
    """Tüm cache'leri temizler. Sadece 'Sistemi Temizle' butonu kullanır."""
    st.cache_data.clear()
    st.cache_resource.clear()
    st.toast("Tüm sistem cache'i temizlendi.", icon="🧹")
