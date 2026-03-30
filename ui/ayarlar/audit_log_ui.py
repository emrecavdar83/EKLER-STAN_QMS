import streamlit as st
import pandas as pd
from sqlalchemy import text
import json
from logic.auth_logic import kullanici_yetkisi_var_mi
from logic.error_handler import handle_exception

def render_audit_log_module(engine):
    """Anayasa v4.0.6: Global Activity Tracker. Güvenlik, Navigasyon ve Hata loglarını gösterir."""
    
    st.header("🛡️ Sistem Günlükleri & Analiz")
    
    # 1. YETKİ KONTROLÜ (RBAC)
    if not kullanici_yetkisi_var_mi("audit_log", "Görüntüle"):
        st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
        return

    tab_audit, tab_errors = st.tabs(["🔒 Aktivite & Güvenlik", "🛠️ Teknik Hatalar (Error Log)"])

    # --- TAB 1: GÜVENLİK VE AKTİVİTE ---
    with tab_audit:
        st.info("💡 Sayfa gezintileri, veri güncellemeleri ve güvenlik olayları takip edilir.")
        col1, col2 = st.columns(2)
        with col1:
            log_tipi = st.multiselect("Olay Tipi", 
                                     ["NAVIGASYON", "OTURUM_ACILDI", "VERI_GUNCELLEME", "VERI_EKLEME", "GIRIS_BASARISIZ", "ERISIM_REDDEDILDI"],
                                     key="audit_multis")
        with col2:
            gun_sayisi = st.slider("Son Kaç Gün?", 1, 30, 7, key="audit_slider")

        try:
            query = "SELECT * FROM sistem_loglari WHERE zaman >= CURRENT_TIMESTAMP - INTERVAL '1 day' * :gun"
            params = {"gun": gun_sayisi}
            if log_tipi:
                query += " AND islem_tipi IN :tipler"; params["tipler"] = tuple(log_tipi)
            query += " ORDER BY zaman DESC LIMIT 200"
            
            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)
                
            if df.empty:
                st.warning("Henüz bir aktivite kaydı bulunamadı.")
            else:
                for idx, row in df.iterrows():
                    icon = "🧭" if row['islem_tipi'] == "NAVIGASYON" else "🔒"
                    with st.expander(f"{icon} [{row['zaman']}] {row['islem_tipi']} | {row['detay'][:50]}..."):
                        c1, c2 = st.columns([2, 1])
                        c1.markdown(f"**📍 Modül:** `{row['modul']}`")
                        c1.markdown(f"**👤 Detay:** {row['detay']}")
                        c2.markdown(f"**🌐 IP:** `{row['ip_adresi']}`")
                        c2.caption(f"📱 Cihaz: {row['cihaz_bilgisi']}")
                        
                        if row['detay_json']:
                            st.divider()
                            st.caption("📋 Veri Değişim Detayı (JSON)")
                            st.json(row['detay_json'])
        except Exception as e:
            handle_exception(e, modul="AUDIT_LOG_UI", tip="UI")

    # --- TAB 2: TEKNİK HATALAR (AI-FRIENDLY) ---
    with tab_errors:
        st.subheader("🚩 AI Destekli Hata Analiz Paneli")
        st.caption("Sistemde oluşan teknik hatalar, stack trace ve AI çözüm önerileri burada listelenir.")

        try:
            h_query = "SELECT * FROM hata_loglari ORDER BY zaman DESC LIMIT 100"
            with engine.connect() as conn:
                df_h = pd.read_sql(text(h_query), conn)

            if df_h.empty:
                st.success("🤖 Harika! Son zamanlarda sistemde hiç teknik hata oluşmadı.")
            else:
                for idx, row in df_h.iterrows():
                    color = "red" if row['seviye'] == "CRITICAL" else "orange"
                    with st.expander(f"🔴 [{row['hata_kodu']}] - {row['modul']} | {row['hata_mesaji'][:80]}...", expanded=(idx==0)):
                        c1, c2 = st.columns([2, 1])
                        c1.markdown(f"**Modül/Fonksiyon:** `{row['modul']}` / `{row['fonksiyon']}`")
                        c1.markdown(f"**Zaman:** `{row['zaman']}`")
                        c2.status(f"Seviye: {row['seviye']}")
                        
                        st.info(f"{row['ai_diagnosis']}")
                        
                        with st.container(border=True):
                            st.caption("🔍 Detaylı Hata İzlemi (Stack Trace)")
                            st.code(row['stack_trace'], language="python")
                            
                        if row['context_data']:
                            with st.expander("📦 Hata Anındaki Veri (Context)"):
                                st.json(row['context_data'])
        except Exception as e:
            st.error(f"Hata logları yüklenemedi: {e}")

if __name__ == "__main__":
    from database.connection import get_engine
    render_audit_log_module(get_engine())
