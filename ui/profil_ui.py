
import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time

from logic.data_fetcher import run_query
from logic.cache_manager import clear_personnel_cache
from logic.auth_logic import _bcrypt_formatinda_mi, get_fallback_info, sifre_hashle

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
    current_db_pass = str(row['sifre']).strip()

    # --- ANAYASA v3.2: GÜVENLİK UYARISI (GRACE PERIOD) ---
    is_encrypted = _bcrypt_formatinda_mi(current_db_pass)
    if not is_encrypted:
        son_tarih = get_fallback_info()
        st.warning(f"""
        🛡️ **Güvenlik Duyurusu:** Hesabınız henüz yeni nesil şifreleme (Bcrypt) zırhına sahip değil. 
        Sistem güvenliği gereği **{son_tarih}** tarihinden itibaren eski tip şifrelerle giriş yapılamayacaktır. 
        Lütfen şifrenizi güncelleyerek hesabınızı korumaya alınız.
        """, icon="⚠️")
    else:
        st.success("✅ Hesabınız Bcrypt şifreleme zırhı ile korunmaktadır.", icon="🛡️")

    with st.form("profilim_update_form"):
        col1, col2 = st.columns(2)
        
        # Salt Okunur Alanlar (Sistem Güvenliği)
        col1.text_input("Ad Soyad", value=row['ad_soyad'], disabled=True)
        col1.text_input("Kullanıcı Adı", value=row['kullanici_adi'], disabled=True)
        col2.text_input("Yetki Rolü", value=row['rol'], disabled=True)
        col2.text_input("Bağlı Olduğu Bölüm", value=row['bolum'], disabled=True)
        
        st.divider()
        
        # Güncellenebilir Alanlar
        c1, c2 = st.columns(2)
        # Eğer şifre hashlenmişse arayüzde temiz göster (veya boş bırak)
        display_pass = "" if is_encrypted else current_db_pass.replace('.0', '')
        # v4.4.2: UI Seviyesinde 72-byte Barajı (max_chars=64)
        new_pass = c1.text_input("🔐 Yeni Şifre", value=display_pass, type="password", key="profilim_new_pass", max_chars=64, help="Şifrenizi değiştirmek istemiyorsanız boş bırakabilirsiniz." if is_encrypted else "Güvenliğiniz için yeni bir şifre belirleyin.")
        new_tel = c2.text_input("📞 Telefon No", value=row['telefon_no'] if pd.notna(row['telefon_no']) else "", key="profilim_tel_no")
        new_servis = st.text_input("🚌 Servis Durağı", value=row['servis_duragi'] if pd.notna(row['servis_duragi']) else "", key="profilim_servis_duragi")

        if st.form_submit_button("🚀 Bilgilerimi Güncelle", use_container_width=True):
            try:
                # Şifre Değişikliği Mantığı
                final_pass = current_db_pass
                if new_pass and new_pass != display_pass:
                    final_pass = sifre_hashle(new_pass)
                
                with engine.begin() as conn:
                    sql = text("""
                        UPDATE personel 
                        SET sifre = :s, telefon_no = :t, servis_duragi = :sd, guncelleme_tarihi = CURRENT_TIMESTAMP 
                        WHERE id = :id
                    """)
                    conn.execute(sql, {"s": final_pass, "t": new_tel, "sd": new_servis, "id": int(p_id)})
                    
                    log_type = 'PROFIL_GUNCELLE_GUVENLI' if new_pass else 'PROFIL_GUNCELLE'
                    log_sql = text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES (:lt, :d)")
                    conn.execute(log_sql, {"lt": log_type, "d": f"Kullanıcı {user_name} (ID: {int(p_id)}) profilini güncelledi. Şifre zırhı: {'AKTİF' if new_pass or is_encrypted else 'PASİF'}"})
                
                clear_personnel_cache()
                st.success("✅ Profiliniz başarıyla güncellendi!")
                st.rerun()
            except Exception as e:
                from logic.error_handler import handle_exception
                handle_exception(e, modul="PROFIL_UI", user_msg="Profil güncellenirken bir sorun oluştu.")
