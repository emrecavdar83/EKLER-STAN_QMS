import streamlit as st
import datetime
from .logic import personel_gorev_getir, yonetici_matris_getir, gorev_tamamla

# EKLERİSTAN A.Ş. 
# Builder Frontend Ajanı Tarafından Streamlit Katmanı

def render_gorevlerim(engine, personel_id, secili_tarih):
    """Personelin kendi üzerine atanan görevleri görüp tamamladığı Zone."""
    st.subheader(f"📅 Görevlerim ({secili_tarih.strftime('%d.%m.%Y')})")
    
    gorevler = personel_gorev_getir(engine, personel_id, str(secili_tarih))
    
    if gorevler.empty:
        st.info("Bu tarih için size atanmış aktif bir görev bulunmamaktadır.")
        return
        
    for idx, g in gorevler.iterrows():
        with st.expander(f"📌 {g['gorev_adi']} [{g['durum']}]", expanded=(g['durum']=='BEKLIYOR')):
            st.write(f"**Kaynak:** {g['gorev_kaynagi']} | **Kategori:** {g.get('kategori', '-')}")
            
            if g['durum'] == 'BEKLIYOR':
                not_key = f"not_{g['id']}"
                sapma_notu = st.text_input("Varsa Sapma/Açıklama Notu:", key=not_key)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Tamamla", key=f"btn_tamam_{g['id']}"):
                        with st.spinner("İşleniyor..."):
                            gorev_tamamla(engine, g['id'], personel_id, sapma_notu)
                        st.success("Görev başarıyla tamamlandı!")
                        st.rerun()
            else:
                st.success(f"Tamamlanma Zamanı: {g['tamamlanma_tarihi']}")
                if g['sapma_notu']:
                    st.warning(f"Not: {g['sapma_notu']}")

def render_yonetici_matrisi(engine, secili_tarih, bolum_id=None):
    """Yöneticilerin veya bölüm sorumlularının X ekseni zaman, Y ekseni personel olan matrisi gördüğü Zone."""
    st.subheader(f"📊 Bölüm Görev ve Akış Matrisi ({secili_tarih.strftime('%d.%m.%Y')})")
    
    matris_data = yonetici_matris_getir(engine, str(secili_tarih), bolum_id)
    
    if matris_data.empty:
        st.info("Bu tarih için havuzda henüz atama bulunamadı.")
        return
        
    # Pandas DataFrame'ini Görselleştirmeye Uygun Hale Getirme
    st.dataframe(
        matris_data[['ad_soyad', 'gorev_adi', 'gorev_kaynagi', 'durum', 'sapma_notu']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "ad_soyad": "Personel",
            "gorev_adi": "Sorumluluk / Düğüm",
            "gorev_kaynagi": "Akış Kaynağı",
            "durum": st.column_config.TextColumn("Durum"),
            "sapma_notu": "Ekstra Not"
        }
    )

def render_gunluk_gorev_modulu(engine):
    """QDMS veya Ana App üzerinden çağrılacak ana render fonksiyonu."""
    st.title("🎯 Birleşik Görev & Akış Yönetimi")
    
    # Session state varsayımı
    current_personel_id = st.session_state.get('personel_id', 1) 
    current_bolum_id = st.session_state.get('bolum_id', None)
    
    secili_tarih = st.date_input("Görev Tarihi", datetime.date.today())
    
    tab1, tab2 = st.tabs(["📝 Benim Görevlerim", "📈 Yönetici Matrisi"])
    
    with tab1:
        render_gorevlerim(engine, current_personel_id, secili_tarih)
        
    with tab2:
        # RBAC Kontrolü örneği
        if st.session_state.get('rol') in ['Admin', 'Yonetici', 'Sorumlu']:
            render_yonetici_matrisi(engine, secili_tarih, current_bolum_id)
        else:
            st.error("Yönetici Matrisi görünümüne yetkiniz bulunmamaktadır.")
