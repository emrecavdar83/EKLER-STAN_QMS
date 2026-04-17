import streamlit as st
import datetime
import pandas as pd
from sqlalchemy import text
from .logic import (
    personel_gorev_getir, yonetici_matris_getir, gorev_tamamla, 
    manuel_gorev_ata, gorev_iptal_et, periyodik_motor_calistir,
    gorev_katalogu_getir, periyodik_kural_ekle
)
from .schema import init_gunluk_gorev_tables

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
        # Öncelik rengi
        onc_emoji = {"KRITIK": "🔴", "NORMAL": "🟡", "DUSUK": "⚪"}.get(g.get('oncelik'), "🟡")
        g_adi = g['ad_ozel'] if g.get('ad_ozel') else g['gorev_adi']
        
        # İptal durumu
        suffix = " [İPTAL EDİLDİ]" if g['durum'] == 'IPTAL' else f" [{g['durum']}]"
        
        with st.expander(f"{onc_emoji} {g_adi}{suffix}", expanded=(g['durum']=='BEKLIYOR')):
            st.write(f"**Kaynak:** {g['gorev_kaynagi']} | **Kategori:** {g.get('kategori', '-')}")
            if g.get('atayan_id'):
                st.caption(f"Atayan ID: {g['atayan_id']}")
            
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
    """Yöneticilerin veya bölüm sorumlularının X ekseni zaman, Y ekseni ayarlar_kullanicilar olan matrisi gördüğü Zone."""
    st.subheader(f"📊 Bölüm Görev ve Akış Matrisi ({secili_tarih.strftime('%d.%m.%Y')})")
    
    matris_data = yonetici_matris_getir(engine, str(secili_tarih), bolum_id)
    
    if matris_data.empty:
        st.info("Bu tarih için havuzda henüz atama bulunamadı.")
        return
        
    # Pandas DataFrame'ini Görselleştirmeye Uygun Hale Getirme
    st.dataframe(
        matris_data[['ad_soyad', 'gorev_adi', 'gorev_kaynagi', 'durum', 'sapma_notu']],
        width="stretch",
        hide_index=True,
        column_config={
            "ad_soyad": "Personel",
            "gorev_adi": "Sorumluluk / Düğüm",
            "gorev_kaynagi": "Akış Kaynağı",
            "durum": st.column_config.TextColumn("Durum"),
            "sapma_notu": "Ekstra Not"
        }
    )
def render_gorev_atama(engine, current_user_id, user_rol, current_bolum_id):
    """Görev atama ekranı."""
    st.subheader("📋 Yeni Görev Ata")
    
    with engine.connect() as conn:
        # 1. Personel Listesi (Hiyerarşi Uyumlu)
        q = "SELECT id, ad_soyad, departman_id FROM ayarlar_kullanicilar WHERE durum = 'AKTİF'"
        if user_rol != 'ADMIN' and current_bolum_id:
            q += f" AND departman_id = {current_bolum_id}"
        personel_df = pd.read_sql(text(q), conn)
        
        # 2. Katalog
        katalog_df = gorev_katalogu_getir(engine)
        
    with st.form("atama_formu"):
        secili_personeller = st.multiselect("Personel(ler)", options=personel_df['id'].tolist(), format_func=lambda x: personel_df[personel_df['id']==x]['ad_soyad'].iloc[0])
        
        v_tipi = st.radio("Görev Tipi", ["KATALOG", "AD-HOC (Özel)"], horizontal=True)
        
        if v_tipi == "KATALOG":
            k_id = st.selectbox("Katalogdan Seç", options=katalog_df['id'].tolist(), format_func=lambda x: katalog_df[katalog_df['id']==x]['ad'].iloc[0])
            ad_ozel = None
        else:
            k_id = None
            ad_ozel = st.text_input("Özel Görev Adı", placeholder="Örn: X Reyonunu Düzenle")
            
        tarih = st.date_input("Hedef/Başlangıç Tarihi", datetime.date.today())
        oncelik = st.selectbox("Öncelik", ["NORMAL", "KRITIK", "DUSUK"])
        
        st.divider()
        is_periodic = st.checkbox("🔄 Bu bir Periyodik/Tekrarlı görev mi?")
        if is_periodic:
            period = st.selectbox("Tekrar Periyodu", ["GUNLUK", "HAFTALIK", "AYLIK", "YILLIK"])
            st.info(f"Bu görev {period} olarak otomatik atanacaktır.")
        else:
            period = None
            
        not_talimat = st.text_area("Ek Talimat/Not")
        
        submitted = st.form_submit_button("🚀 İşlemi Tamamla")
        if submitted:
            if not secili_personeller:
                st.error("En az bir ayarlar_kullanicilar seçmelisiniz.")
            elif v_tipi == "AD-HOC (Özel)" and not ad_ozel:
                st.error("Özel görev adı boş olamaz.")
            else:
                if is_periodic:
                    kural_verisi = {
                        "personel_ids": secili_personeller,
                        "kaynak_tipi": "KATALOG" if v_tipi=="KATALOG" else "AD-HOC",
                        "kaynak_id": k_id,
                        "ad_ozel": ad_ozel,
                        "oncelik": oncelik,
                        "periyot_tipi": period,
                        "periyot_detay": "{}"
                    }
                    periyodik_kural_ekle(engine, kural_verisi)
                    st.success(f"Periyodik kural {len(secili_personeller)} ayarlar_kullanicilar için kaydedildi.")
                else:
                    atama_verisi = {
                        "personel_ids": secili_personeller,
                        "v_tipi": "KATALOG" if v_tipi=="KATALOG" else "AD-HOC",
                        "kaynak_id": k_id,
                        "ad_ozel": ad_ozel,
                        "tarih": str(tarih),
                        "oncelik": oncelik,
                        "atayan_id": current_user_id
                    }
                    manuel_gorev_ata(engine, atama_verisi)
                    st.success(f"{len(secili_personeller)} personele manuel görev atandı!")
                st.rerun()

def render_gunluk_gorev_modulu(engine):
    """QDMS veya Ana App üzerinden çağrılacak ana render fonksiyonu."""
    try:
        st.title("🎯 Birleşik Görev & Akış Yönetimi")
        
        # 🧪 SELF-HEALING: Tabloları garanti et (Hataları yutmaz)
        init_gunluk_gorev_tables(engine)
        
        # Veritabanından ayarlar_kullanicilar bilgilerini çek
        username = st.session_state.get('user', '')
        current_personel_id = 1
        current_bolum_id = None
        
        if username:
            with engine.connect() as conn:
                user_data = conn.execute(text("SELECT id, departman_id FROM ayarlar_kullanicilar WHERE kullanici_adi = :u"), {"u": username}).fetchone()
                if user_data:
                    current_personel_id = user_data[0]
                    current_bolum_id = user_data[1]
        
        periyodik_motor_calistir(engine)
        
        secili_tarih = st.date_input("Görev Tarihi", datetime.date.today())
        
        # Rol ve Yetki Kontrolü
        raw_rol = st.session_state.get('user_rol', '')
        if hasattr(raw_rol, 'iloc'): 
            user_rol = str(raw_rol.iloc[0]).strip().upper()
        else:
            user_rol = str(raw_rol).strip().upper()
            
        is_manager = user_rol in ['ADMIN', 'YONETICI', 'SORUMLU']
        
        tabs = ["📝 Benim Görevlerim", "📈 Yönetici Matrisi"]
        if is_manager:
            tabs.append("➕ Görev Atama")
            
        t_list = st.tabs(tabs)
        
        with t_list[0]:
            render_gorevlerim(engine, current_personel_id, secili_tarih)
            
        if is_manager:
            with t_list[1]:
                render_yonetici_matrisi(engine, secili_tarih, current_bolum_id)
            with t_list[2]:
                render_gorev_atama(engine, current_personel_id, user_rol, current_bolum_id)
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="GOREV_MAIN", tip="UI")

