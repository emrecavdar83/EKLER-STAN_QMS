# modules/performans/performans_sayfasi.py
import streamlit as st
import pandas as pd
from datetime import datetime
from . import performans_db as db
from . import performans_form as form
from . import performans_sabitleri as sabit
from database.connection import get_engine
from logic.auth_logic import kullanici_yetkisi_var_mi

def performans_sayfasi_goster():
    try:
        st.title("📊 Performans & Polivalans Yönetimi")
        st.caption("BRC v9 & IFS v8 Uyumlu Personel Yetkinlik Takibi")
        
        engine = get_engine()
        
        # Yetki Kontrolü
        if not kullanici_yetkisi_var_mi("Performans & Polivalans", "Görüntüle"):
            st.error("Bu modüle erişim yetkiniz yok.")
            return

        tabs = st.tabs(["➕ Yeni Değerlendirme", "📋 Geçmiş Kayıtlar", "📈 Analiz & Matris"])
        
        # --- TAB 1: YENİ DEĞERLENDİRME ---
        with tabs[0]:
            if not kullanici_yetkisi_var_mi("Performans & Polivalans", "Düzenle"):
                st.warning("Değerlendirme girmek için 'Düzenle' yetkisi gereklidir.")
            else:
                p_df = db.personel_listesi_getir(engine)
                bilgi = form.calisan_bilgi_formu(p_df)
                
                if bilgi:
                    puanlar = form.puan_giris_formu()
                    sonuc = form.degerlendirme_ozet_karti(puanlar)
                    
                    yorum = st.text_area("🗒️ Değerlendirme Yorumu & Notlar")
                    
                    if st.button("💾 DEĞERLENDİRMEYİ KAYDET", use_container_width=True, type="primary"):
                        # Veriyi birleştir
                        final_data = {**bilgi, **puanlar, **sonuc}
                        final_data['yorum'] = yorum
                        final_data['degerlendiren_adi'] = st.session_state.get('user', 'Sistem')
                        final_data['guncelleyen_kullanici'] = st.session_state.get('user', 'Sistem')
                        
                        ok, msg = db.degerlendirme_kaydet(engine, final_data)
                        if ok:
                            st.success(msg)
                            st.balloons()
                        else:
                            st.error(msg)

        # --- TAB 2: GEÇMİŞ KAYITLAR ---
        with tabs[1]:
            st.subheader("🔍 Kayıt Sorgulama")
            c1, c2 = st.columns(2)
            f_bolum = c1.selectbox("Bölüm Filtresi", ["Tümü"] + db.bolum_listesi_getir(engine))
            f_yil = c2.number_input("Yıl Filtresi", 2020, 2100, datetime.now().year, key="f_yil")
            
            filtre = {}
            if f_bolum != "Tümü": filtre['bolum'] = f_bolum
            filtre['yil'] = f_yil
            
            liste_df = db.degerlendirme_listele(engine, filtre)
            if not liste_df.empty:
                st.dataframe(liste_df[[
                    'degerlendirme_tarihi', 'calisan_adi_soyadi', 'bolum', 
                    'agirlikli_toplam_puan', 'polivalans_duzeyi', 'degerlendiren_adi'
                ]], use_container_width=True, hide_index=True)
            else:
                st.info("Kayıt bulunamadı.")

        # --- TAB 3: ANALİZ & MATRİS ---
        with tabs[2]:
            st.info("Polivalans Matrisi ve Trend Analizleri bir sonraki güncellemede aktif edilecektir.")
            # Burada pivot tablolar ve polivalans renk matrisi gelecek.
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="PERFORMANS_MAIN", tip="UI")
