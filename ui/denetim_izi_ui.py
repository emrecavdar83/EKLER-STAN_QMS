import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
import pytz
from logic.auth_logic import kullanici_yetkisi_var_mi
from logic.error_handler import handle_exception

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

def render_denetim_izi_module(engine):
    """
    Anayasa v5.8.9: Yönetim (MGT) bölgesi için Sistem Audit Trail (Denetim İzi) paneli.
    Bu dashboard, yöneticilerin kritik sistem hareketlerini izlemesini sağlar.
    """
    try:
        # MGT Zone için Yetki Kontrolü
        if not kullanici_yetkisi_var_mi("👁️ Denetim İzi", "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.stop()

        st.title("👁️ Sistem Denetim İzi (Audit Trail)")
        st.caption("EKLERİSTAN QMS — Yönetim İzleme ve Uyum Paneli (Read-Only)")

        tab_aktivite, tab_kpi_red, tab_belge = st.tabs([
            "🔍 Sistem Aktiviteleri", 
            "❌ Kalite (KPI) İhlalleri", 
            "📄 Belge & QDMS Geçmişi"
        ])

        # --- 1. SİSTEM AKTİVİTELERİ ---
        with tab_aktivite:
            col1, col2 = st.columns(2)
            gun_sayisi = col1.slider("Geçmiş Görüntüleme (Gün)", 1, 30, 3)
            filtre_islem_tipi = col2.multiselect(
                "İşlem Tipi Filtresi", 
                ["VERI_EKLEME", "VERI_GUNCELLEME", "GIRIS_BASARISIZ", "OTURUM_ACILDI", "VERI_SILME"],
                default=["VERI_EKLEME", "VERI_GUNCELLEME", "VERI_SILME"]
            )

            is_pg = engine.dialect.name == 'postgresql'
            if is_pg:
                tarih_filtre = f"zaman >= CURRENT_TIMESTAMP - INTERVAL '{gun_sayisi} days'"
            else:
                tarih_filtre = f"zaman >= datetime('now', '-{gun_sayisi} days')"

            if filtre_islem_tipi:
                pl = ", ".join([f":t{i}" for i in range(len(filtre_islem_tipi))])
                tip_filtre = f"AND islem_tipi IN ({pl})"
                params = {f"t{i}": v for i, v in enumerate(filtre_islem_tipi)}
            else:
                tip_filtre = ""
                params = {}

            # Güvenlik ve aktivite logları
            query = f"""
                SELECT zaman, islem_tipi, modul, detay, ip_adresi, cihaz_bilgisi 
                FROM sistem_loglari 
                WHERE {tarih_filtre} {tip_filtre} 
                ORDER BY zaman DESC 
                LIMIT 300
            """
            with engine.connect() as conn:
                df_log = pd.read_sql(text(query), conn, params=params)

            if df_log.empty:
                st.info("Bu kriterlere uygun log kaydı bulunamadı.")
            else:
                st.dataframe(df_log, width="stretch", hide_index=True)

        # --- 2. KALİTE İHLALLERİ ---
        with tab_kpi_red:
            st.subheader("🔴 Son 14 Günlük Reddedilen Kalite Kayıtları")
            kpi_query = """
                SELECT tarih, saat, urun_adi, miktar, karar, kullanici, notlar, vardiya 
                FROM urun_kpi_kontrol 
                WHERE karar = 'RED' AND tarih >= date('now', '-14 days') 
                ORDER BY tarih DESC, saat DESC
            """ if not is_pg else """
                SELECT tarih, saat, urun_adi, miktar, karar, kullanici, notlar, vardiya 
                FROM urun_kpi_kontrol 
                WHERE karar = 'RED' AND tarih >= CURRENT_DATE - INTERVAL '14 days' 
                ORDER BY tarih DESC, saat DESC
            """
            try:
                with engine.connect() as conn:
                    df_kpi = pd.read_sql(text(kpi_query), conn)
                
                if df_kpi.empty:
                    st.success("✅ Son 14 günde reddedilen bir kalite işlemi bulunmuyor.")
                else:
                    st.warning(f"Olası kritik durumlar: {len(df_kpi)} RED kararı bulundu.")
                    st.dataframe(df_kpi, width="stretch", hide_index=True)
            except Exception as e:
                st.error("Veri alınamadı: Tablo uyumsuz veya boş.")

        # --- 3. QDMS GEÇMİŞİ ---
        with tab_belge:
            st.subheader("📄 Açık ve Taslak Durumundaki Dökümanlar")
            belge_query = "SELECT belge_kodu, belge_adi, belge_tipi, durum, olusturma_tarihi FROM qdms_belgeler WHERE durum IN ('taslak', 'incelemede') ORDER BY olusturma_tarihi DESC"
            try:
                with engine.connect() as conn:
                    df_belge = pd.read_sql(text(belge_query), conn)
                if df_belge.empty:
                    st.info("Sistemde taslak belge bulunmuyor.")
                else:
                    st.dataframe(df_belge, width="stretch", hide_index=True)
            except Exception:
                st.info("QDMS verilerine ulaşılamadı.")

    except Exception as e:
        handle_exception(e, modul="DENETIM_IZI_UI", tip="UI")
