import streamlit as st
import pandas as pd
from datetime import datetime
import json
import re
import os
import pytz
from sqlalchemy import text

from logic.data_fetcher import run_query, get_all_sub_department_ids
from ui.raporlar.report_utils import _rapor_excel_export, _get_personnel_display_map, _generate_base_html, get_istanbul_time

def render_kalite_sub_module(engine, bas_tarih, bit_tarih, matrix_filters, specific=None):
    st.subheader("🛡️ Kalite & Gıda Güvenliği Raporları")
    
    if specific == "temizlik":
        _render_temizlik_raporu(engine, bas_tarih, bit_tarih)
        return

    tab1, tab2, tab3 = st.tabs(["🍩 KPI Analizi", "🧹 Temizlik Takip", "📅 Günlük Operasyon Özeti"])
    
    with tab1:
        _render_kpi_raporu(engine, bas_tarih, bit_tarih)
    
    with tab2:
        _render_temizlik_raporu(engine, bas_tarih, bit_tarih)
        
    with tab3:
        _render_gunluk_operasyonel_rapor(engine, bas_tarih, matrix_filters)

def _render_kpi_raporu(engine, bas_tarih, bit_tarih):
    sql = f"SELECT * FROM urun_kpi_kontrol WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'"
    df = run_query(sql)
    if df.empty:
        st.warning("Bu tarih aralığında kalite kaydı bulunamadı."); return

    df.columns = [c.lower() for c in df.columns]
    p_map = _get_personnel_display_map(run_query, engine)

    onay_s = len(df[df['karar'] == 'ONAY'])
    red_s  = len(df[df['karar'] == 'RED'])
    k1, k2, k3 = st.columns(3)
    k1.success(f"Onaylanan: {onay_s}")
    k2.error(f"Reddedilen: {red_s}")
    k3.info(f"Toplam: {len(df)}")

    urunler = sorted(df['urun_adi'].dropna().unique().tolist() if 'urun_adi' in df.columns else df['urun'].dropna().unique().tolist())
    urun_sec = st.selectbox("Ürün Filtresi", ["(Tümü)"] + urunler)
    
    col_name = 'urun_adi' if 'urun_adi' in df.columns else 'urun'
    df_urun = df if urun_sec == "(Tümü)" else df[df[col_name] == urun_sec]

    st.dataframe(df_urun, width="stretch", hide_index=True)
    _rapor_excel_export(st, df_urun, None, f"KPI_{urun_sec}", bas_tarih, bit_tarih)

    # HTML/PDF
    html_rapor = _kpi_html_raporu_olustur(df_urun, urun_sec, bas_tarih, bit_tarih, p_map)
    html_json = json.dumps(html_rapor)
    pdf_js = f"<script>function p(){{var w=window.open('','_blank');w.document.write({html_json});w.document.close();setTimeout(function(){{w.print();}},600);}}</script><button onclick='p()' style='width:100%;padding:10px;background:#8B0000;color:white;border:none;border-radius:5px;cursor:pointer;'>🖨️ PDF Raporu Oluştur</button>"
    st.components.v1.html(pdf_js, height=60)

def _kpi_html_raporu_olustur(df_urun, urun_sec, bas_tarih, bit_tarih, personel_map):
    # (Simplified version of the complex HTML logic from raporlama_ui.py to save space but keep visual quality)
    rapor_tarihi = get_istanbul_time().strftime('%d.%m.%Y %H:%M')
    # ... logic for rows ...
    trs = ""
    for _, row in df_urun.iterrows():
        karar = str(row.get('karar', '-'))
        clr = "green" if karar == "ONAY" else "red"
        trs += f"<tr><td>{row.get('tarih','')}</td><td>{row.get( 'urun_adi' if 'urun_adi' in row else 'urun' ,'-')}</td><td>{row.get('miktar',0)}</td><td style='color:{clr}'>{karar}</td><td>{row.get('kullanici','-')}</td></tr>"
    
    content = f"<table><thead><tr><th>Tarih</th><th>Ürün</th><th>Miktar</th><th>Karar</th><th>Personel</th></tr></thead><tbody>{trs}</tbody></table>"
    cards = f"<div class='ozet-kart toplam'>Toplam: {len(df_urun)}</div>"
    sigs = "<div class='imza-kutu'><b>Kalite Sorumlusu</b><br><br>İmza</div>"
    
    return _generate_base_html("KALİTE KONTROL ANALİZ RAPORU", "EKL-KYS-KPI-001", f"{bas_tarih} / {bit_tarih}", cards, content, sigs)

def _render_temizlik_raporu(engine, bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM temizlik_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("⚠️ Seçilen tarihlerde temizlik kaydı bulunamadı."); return

    p_map = _get_personnel_display_map(run_query, engine)
    if 'kullanici' in df.columns:
        df['kullanici'] = df['kullanici'].astype(str).map(lambda x: p_map.get(x, x))

    st.dataframe(df, width="stretch", hide_index=True)
    _rapor_excel_export(st, df, None, "Temizlik_Raporu", bas_tarih, bit_tarih)

def _render_gunluk_operasyonel_rapor(engine, bas_tarih, matrix_filters):
    st.info(f"📅 **{bas_tarih}** tarihli operasyon özeti.")
    t_str = str(bas_tarih)
    
    # Simple summary metric view
    kpi_df = run_query(f"SELECT * FROM urun_kpi_kontrol WHERE tarih='{t_str}'")
    sosts_df = run_query(f"SELECT * FROM sicaklik_olcumleri WHERE DATE(olcum_zamani)='{t_str}'" if "sqlite" in str(engine.url) else f"SELECT * FROM sicaklik_olcumleri WHERE olcum_zamani::date='{t_str}'")
    
    m1, m2 = st.columns(2)
    m1.metric("KPI Kaydı", len(kpi_df))
    m2.metric("Sıcaklık Kaydı", len(sosts_df))
    
    if not kpi_df.empty:
        st.write("### Günlük Detaylar")
        st.dataframe(kpi_df[['urun_adi', 'karar', 'kullanici']] if 'urun_adi' in kpi_df.columns else kpi_df[['urun', 'karar', 'kullanici']], width="stretch")
