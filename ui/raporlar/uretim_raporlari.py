import streamlit as st
import pandas as pd
from datetime import datetime
import json
from sqlalchemy import text

from logic.data_fetcher import run_query, get_all_sub_department_ids
from ui.raporlar.report_utils import _rapor_excel_export, _get_personnel_display_map, _generate_base_html

def render_uretim_sub_module(engine, bas_tarih, bit_tarih, matrix_filters):
    st.subheader("🏭 Üretim & Verimlilik Raporları")
    
    tab1, tab2 = st.tabs(["📊 Genel Üretim Verimliliği", "📦 MAP Üretim Detayları"])
    
    with tab1:
        _render_uretim_raporu(engine, bas_tarih, bit_tarih, matrix_filters)
    
    with tab2:
        _render_map_raporlari(engine, bas_tarih, bit_tarih)

def _render_uretim_raporu(engine, bas_tarih, bit_tarih, matrix_filters=None):
    saha_id = matrix_filters.get("saha") if matrix_filters else 0
    dept_id = matrix_filters.get("dept") if matrix_filters else 0
    
    personel_filter = ""
    if saha_id > 0:
        personel_filter += f" AND (p.operasyonel_bolum_id = {saha_id})"
    if dept_id > 0:
        all_depts = get_all_sub_department_ids(dept_id)
        personel_filter += f" AND (p.departman_id IN ({','.join(map(str, all_depts))}))"

    sql = f"""
        SELECT d.* FROM depo_giris_kayitlari d 
        LEFT JOIN personel p ON d.kullanici = p.kullanici_adi 
        WHERE d.tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}' {personel_filter}
    """
    df = run_query(sql)
    if df.empty:
        st.warning("Bu kriterlere uygun üretim kaydı bulunamadı."); return

    df.columns = [c.lower() for c in df.columns]
    
    toplam_miktar = df['miktar'].sum()
    toplam_fire = df['fire'].sum()
    fire_oran = (toplam_fire / toplam_miktar * 100) if toplam_miktar > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Üretim", f"{toplam_miktar:,} Adet")
    m2.metric("Toplam Fire", f"{toplam_fire:,} Adet")
    m3.metric("Fire Oranı", f"%{fire_oran:.2f}")

    st.dataframe(df, use_container_width=True, hide_index=True)
    _rapor_excel_export(st, df, None, "Uretim_Verimlilik_Raporu", bas_tarih, bit_tarih)

def _render_map_raporlari(engine, bas_tarih, bit_tarih):
    st.subheader("📦 MAP Makinası Üretim Raporları")
    # v5.0: Modular MAP link
    import ui.map_uretim.map_rapor_pdf as mpdf
    
    sql = f"""
        SELECT v.* FROM map_vardiya v
        WHERE v.tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}' AND v.durum='KAPALI'
        ORDER BY v.tarih DESC
    """
    df = run_query(sql)
    if df.empty:
        st.info("Bu tarihlerde kapalı MAP vardiyası bulunamadı."); return

    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("🖨️ Seçili Vardiya Raporlarını Hazırla"):
         st.info("ID bazlı PDF üretimi desteklenmektedir.")
