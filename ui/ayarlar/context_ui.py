import streamlit as st
from logic.context_manager import tümünü_senkronize_et, ajanlara_baglam_ekle, registry_oku
import os
from datetime import datetime

# EKLERİSTAN QMS 
# Faz 2.3: Context UI

def render_context_tab(engine):
    """Bağlam yönetimi arayüzünü oluşturur."""
    st.subheader("📚 Dinamik Dokümantasyon Bağlamı (Context7)")
    st.info("Ajanların (Builder, Tester) güncel resmi API dokümantasyonuna erişimini buradan yönetebilirsiniz.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Tüm Dökümanları Güncelle", width="stretch"):
            with st.spinner("Dokümanlar indiriliyor ve temizleniyor..."):
                tümünü_senkronize_et()
            st.success("Tüm dokümanlar başarıyla senkronize edildi.")
    
    with col2:
        if st.button("🔗 Ajanlara Bağlam Enjekte Et", width="stretch"):
            ajanlara_baglam_ekle()
            st.success("Ajan CLAUDE.md dosyaları güncellendi.")

    st.markdown("---")
    st.write("### 📊 Mevcut Bağlam Durumu")
    _render_status_table()

def _render_status_table():
    """Cache dizinindeki dökümanların durumunu tablolaştırır."""
    registry = registry_oku()
    data = []
    for lib in registry.keys():
        yol = f".antigravity/context/cache/{lib}/"
        status = "❌ Eksik"
        last_up = "-"
        if os.path.exists(yol):
            files = os.listdir(yol)
            if files:
                status = f"✅ Hazır ({len(files)} Parça)"
                mtime = os.path.getmtime(yol)
                last_up = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        
        data.append({"Kütüphane": lib.upper(), "Durum": status, "Son Güncelleme": last_up})
    
    st.table(data)
