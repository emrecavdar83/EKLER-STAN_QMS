import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
import pytz
from logic.auth_logic import kullanici_yetkisi_var_mi
from logic.error_handler import handle_exception
from constants import AUDIT_LOG_LIMIT

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

def _render_aktivite_tab(engine, is_pg):
    col1, col2 = st.columns(2)
    gun_sayisi = col1.slider("Geçmiş Görüntüleme (Gün)", 1, 30, 3)
    filtre = col2.multiselect("İşlem Tipi Filtresi",
        ["VERI_EKLEME", "VERI_GUNCELLEME", "GIRIS_BASARISIZ", "OTURUM_ACILDI", "VERI_SILME"],
        default=["VERI_EKLEME", "VERI_GUNCELLEME", "VERI_SILME"])
    tarih_f = (f"zaman >= CURRENT_TIMESTAMP - INTERVAL '{gun_sayisi} days'" if is_pg
               else f"zaman >= datetime('now', '-{gun_sayisi} days')")
    if filtre:
        pl = ", ".join([f":t{i}" for i in range(len(filtre))])
        tip_f, params = f"AND islem_tipi IN ({pl})", {f"t{i}": v for i, v in enumerate(filtre)}
    else:
        tip_f, params = "", {}
    q = f"SELECT zaman, islem_tipi, modul, detay, ip_adresi, cihaz_bilgisi FROM sistem_loglari WHERE {tarih_f} {tip_f} ORDER BY zaman DESC LIMIT {AUDIT_LOG_LIMIT}"
    with engine.connect() as conn:
        df = pd.read_sql(text(q), conn, params=params)
    st.dataframe(df, width="stretch", hide_index=True) if not df.empty else st.info("Bu kriterlere uygun log kaydı bulunamadı.")


def _render_kpi_red_tab(engine, is_pg):
    st.subheader("🔴 Son 14 Günlük Reddedilen Kalite Kayıtları")
    q = ("""SELECT tarih, saat, urun_adi, miktar, karar, kullanici, notlar, vardiya FROM urun_kpi_kontrol
             WHERE karar = 'RED' AND tarih >= CURRENT_DATE - INTERVAL '14 days' ORDER BY tarih DESC, saat DESC"""
         if is_pg else
         """SELECT tarih, saat, urun_adi, miktar, karar, kullanici, notlar, vardiya FROM urun_kpi_kontrol
             WHERE karar = 'RED' AND tarih >= date('now', '-14 days') ORDER BY tarih DESC, saat DESC""")
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(q), conn)
        if df.empty:
            st.success("✅ Son 14 günde reddedilen bir kalite işlemi bulunmuyor.")
        else:
            st.warning(f"Olası kritik durumlar: {len(df)} RED kararı bulundu.")
            st.dataframe(df, width="stretch", hide_index=True)
    except Exception:
        st.error("Veri alınamadı: Tablo uyumsuz veya boş.")


def _render_belge_tab(engine):
    st.subheader("📄 Açık ve Taslak Durumundaki Dökümanlar")
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT belge_kodu, belge_adi, belge_tipi, durum, olusturma_tarihi FROM qdms_belgeler WHERE durum IN ('taslak', 'incelemede') ORDER BY olusturma_tarihi DESC"), conn)
        st.dataframe(df, width="stretch", hide_index=True) if not df.empty else st.info("Sistemde taslak belge bulunmuyor.")
    except Exception:
        st.info("QDMS verilerine ulaşılamadı.")


def render_denetim_izi_module(engine):
    try:
        if not kullanici_yetkisi_var_mi("👁️ Denetim İzi", "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()
        st.title("👁️ Sistem Denetim İzi (Audit Trail)")
        st.caption("EKLERİSTAN QMS — Yönetim İzleme ve Uyum Paneli (Read-Only)")
        is_pg = engine.dialect.name == 'postgresql'
        tab_a, tab_k, tab_b = st.tabs(["🔍 Sistem Aktiviteleri", "❌ Kalite (KPI) İhlalleri", "📄 Belge & QDMS Geçmişi"])
        with tab_a: _render_aktivite_tab(engine, is_pg)
        with tab_k: _render_kpi_red_tab(engine, is_pg)
        with tab_b: _render_belge_tab(engine)
    except Exception as e:
        handle_exception(e, modul="DENETIM_IZI_UI", tip="UI")
