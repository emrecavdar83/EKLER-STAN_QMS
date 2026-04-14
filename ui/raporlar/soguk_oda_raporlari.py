import streamlit as st
import pandas as pd
from datetime import datetime
import json
import plotly.express as px
import pytz
import time
from sqlalchemy import text

from logic.data_fetcher import run_query
from ui.raporlar.report_utils import _rapor_excel_export, _get_personnel_display_map, get_istanbul_time
from soguk_oda_utils import get_matrix_data, get_trend_data

def render_soguk_oda_sub_module(engine, bas_tarih, bit_tarih):
    st.subheader("❄️ Soğuk Zincir Takip Raporları")
    
    tab1, tab2 = st.tabs(["📊 Günlük İzleme Matrisi", "📈 Sıcaklık Trend Analizi"])
    
    with tab1:
        _render_soguk_oda_izleme(engine, bas_tarih, bit_tarih)
    
    with tab2:
        _render_soguk_oda_trend(engine)

def _render_soguk_oda_izleme(engine, bas_tarih, bit_tarih):
    st.info("❄️ Günlük Sıcaklık İzleme (Matris Görünümü)")
    
    df_matris = get_matrix_data(engine, bas_tarih, bit_tarih)
    if df_matris.empty:
        st.warning("Bu tarih için henüz planlanmış ölçüm bulunmuyor."); return

    # Matrix representation logic (Simplified for consistency)
    st.dataframe(df_matris, width="stretch", hide_index=True)
    
    _rapor_excel_export(st, df_matris, None, "Soguk_Oda_İzleme", bas_tarih, bit_tarih)

    # PDF Buttons for each room
    unique_rooms = df_matris['oda_adi'].unique()
    cols = st.columns(3)
    p_map = _get_personnel_display_map(run_query, engine)
    
    for idx, oda in enumerate(unique_rooms):
        if cols[idx % 3].button(f"📄 {oda} PDF Raporu", key=f"pdf_{oda}"):
            st.info(f"{oda} için PDF raporu hazırlanıyor...")

def _render_soguk_oda_trend(engine):
    st.subheader("📈 Sıcaklık Trend Analizi")
    rooms = run_query("SELECT id, oda_adi FROM soguk_odalar WHERE durum = 'AKTİF'")
    if rooms.empty:
        st.info("Kayıtlı aktif oda bulunamadı."); return
        
    target = st.selectbox("Oda Seçiniz", rooms['id'], format_func=lambda x: rooms[rooms['id']==x]['oda_adi'].iloc[0])
    df = get_trend_data(engine, target)
    
    if not df.empty:
        fig = px.line(df, x='olcum_zamani', y='sicaklik_degeri', title=f"{rooms[rooms['id']==target]['oda_adi'].iloc[0]} Trendi")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Kayıtlı trend verisi bulunamadı.")
