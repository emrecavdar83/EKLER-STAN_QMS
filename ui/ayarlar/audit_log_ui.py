import streamlit as st
import pandas as pd
from sqlalchemy import text
from logic.auth_logic import kullanici_yetkisi_var_mi

def render_audit_log_module(engine):
    """Anayasa v3.2: Güvenlik loglarını gösteren admin modülü."""
    
    st.header("🛡️ Güvenlik Denetim Logları (Audit Log)")
    
    # 1. YETKİ KONTROLÜ (Zero Hardcode - RBAC)
    if not kullanici_yetkisi_var_mi("audit_log", "Görüntüle"):
        st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
        return

    st.info("💡 Bu ekranda başarısız giriş denemeleri, yetkisiz erişim talepleri ve şifre değişiklikleri takip edilir.")

    # 2. FİLTRELER
    col1, col2 = st.columns(2)
    with col1:
        log_tipi = st.multiselect("Olay Tipi", 
                                 ["GIRIS_BASARISIZ", "ERISIM_REDDEDILDI", "SIFRE_HASH_MIGRATION", "ROL_GUNCELLEMESI", "OTURUM_ZORLA_KAPATILDI", "HASH_HATA"],
                                 default=[])
    with col2:
        gun_sayisi = st.slider("Son Kaç Gün?", 1, 30, 7)

    # 3. VERİ ÇEKME
    try:
        query = """
            SELECT zaman, islem_tipi, detay 
            FROM sistem_loglari 
            WHERE zaman >= CURRENT_TIMESTAMP - INTERVAL '1 day' * :gun
        """
        params = {"gun": gun_sayisi}
        
        if log_tipi:
            query += " AND islem_tipi IN :tipler"
            params["tipler"] = tuple(log_tipi)
            
        query += " ORDER BY zaman DESC LIMIT 500"
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            
        if df.empty:
            st.warning("Seçilen kriterlere uygun log kaydı bulunamadı.")
        else:
            # Görselleştirme
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Logları CSV Olarak İndir", csv, "audit_logs.csv", "text/csv")
            
    except Exception as e:
        st.error(f"Loglar yüklenirken bir hata oluştu: {e}")

if __name__ == "__main__":
    from database.connection import get_engine
    render_audit_log_module(get_engine())
