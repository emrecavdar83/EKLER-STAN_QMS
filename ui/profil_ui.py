
import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time

from logic.data_fetcher import run_query
from logic.cache_manager import clear_personnel_cache

def render_profil_modulu(engine):
    st.title("👤 Profilim ve Güvenlik")
    st.info("Kişisel bilgilerinizi ve şifrenizi buradan güncelleyebilirsiniz.")

    user_name = st.session_state.get('user')
    if not user_name:
        st.error("Oturum bilgisi bulunamadı.")
        return

    # Mevcut kullanıcı bilgilerini getir
    user_data = run_query("SELECT id, ad_soyad, kullanici_adi, sifre, rol, bolum, telefon_no, servis_duragi FROM personel WHERE kullanici_adi = :u", {"u": user_name})
    
    if user_data.empty:
        st.warning("Kullanıcı detayları bulunamadı.")
        return

    row = user_data.iloc[0]
    p_id = row['id']

    with st.form("profil_update_form"):
        col1, col2 = st.columns(2)
        
        # Salt Okunur Alanlar (Sistem Güvenliği)
        col1.text_input("Ad Soyad", value=row['ad_soyad'], disabled=True)
        col1.text_input("Kullanıcı Adı", value=row['kullanici_adi'], disabled=True)
        col2.text_input("Yetki Rolü", value=row['rol'], disabled=True)
        col2.text_input("Bağlı Olduğu Bölüm", value=row['bolum'], disabled=True)
        
        st.divider()
        
        # Güncellenebilir Alanlar
        c1, c2 = st.columns(2)
        new_pass = c1.text_input("🔐 Yeni Şifre", value=str(row['sifre']).strip().replace('.0', ''), type="password")
        new_tel = c2.text_input("📞 Telefon No", value=row['telefon_no'] if pd.notna(row['telefon_no']) else "")
        new_servis = st.text_input("🚌 Servis Durağı", value=row['servis_duragi'] if pd.notna(row['servis_duragi']) else "")

        if st.form_submit_button("🚀 Bilgilerimi Güncelle", use_container_width=True):
            try:
                with engine.begin() as conn:
                    sql = text("""
                        UPDATE personel 
                        SET sifre = :s, telefon_no = :t, servis_duragi = :sd, guncelleme_tarihi = CURRENT_TIMESTAMP 
                        WHERE id = :id
                    """)
                    conn.execute(sql, {"s": new_pass, "t": new_tel, "sd": new_servis, "id": p_id})
                    
                    log_sql = text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('PROFIL_GUNCELLE', :d)")
                    conn.execute(log_sql, {"d": f"Kullanıcı {user_name} kendi profil bilgilerini güncelledi."})
                
                clear_personnel_cache()
                st.success("✅ Profiliniz başarıyla güncellendi!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Güncelleme sırasında hata oluştu: {e}")
