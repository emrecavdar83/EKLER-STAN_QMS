import streamlit as st
import pandas as pd
from datetime import datetime
import json
from sqlalchemy import text

from logic.data_fetcher import run_query, get_all_sub_department_ids
from ui.raporlar.report_utils import _rapor_excel_export, _get_personnel_display_map, _generate_base_html
from ui.raporlar.islem_raporlari import render_islem_gecmisi_tab

def render_uretim_sub_module(engine, bas_tarih, bit_tarih, matrix_filters):
    st.subheader("🏭 Üretim & Verimlilik Raporları")
    
    tab1, tab2, tab3 = st.tabs(["📊 Genel Üretim Verimliliği", "📦 MAP Üretim Detayları", "🔍 İşlem Geçmişi"])
    
    with tab1:
        _render_uretim_raporu(engine, bas_tarih, bit_tarih, matrix_filters)
    
    with tab2:
        _render_map_raporlari(engine, bas_tarih, bit_tarih)
        
    with tab3:
        render_islem_gecmisi_tab(engine, "uretim_girisi", bas_tarih, bit_tarih)

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
        LEFT JOIN ayarlar_kullanicilar p ON d.kullanici = p.kullanici_adi 
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

    st.dataframe(df, width="stretch", hide_index=True)
    _rapor_excel_export(st, df, None, "Uretim_Verimlilik_Raporu", bas_tarih, bit_tarih)

def _render_map_raporlari(engine, bas_tarih, bit_tarih):
    st.subheader("📦 MAP Makinası Üretim Raporları")
    # v6.5.2: Gelişmiş Rapor Akışı (Üretim + Fire + Ürün Entegrasyonu)
    
    sql = f"""
        SELECT 
            v.id, v.tarih, v.makina_no, v.vardiya_no, v.urun_adi, 
            v.gerceklesen_uretim as uretim,
            COALESCE(f.toplam_fire, 0) as fire,
            CASE 
                WHEN v.gerceklesen_uretim > 0 THEN ROUND(CAST(CAST(COALESCE(f.toplam_fire, 0) AS FLOAT) / (v.gerceklesen_uretim + COALESCE(f.toplam_fire, 0)) * 100 AS NUMERIC), 2)
                ELSE 0 
            END as fire_oran_pct
        FROM map_vardiya v
        LEFT JOIN (
            SELECT vardiya_id, SUM(miktar_adet) as toplam_fire 
            FROM map_fire_kaydi 
            GROUP BY vardiya_id
        ) f ON v.id = f.vardiya_id
        WHERE v.tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}' AND v.durum='KAPALI'
        ORDER BY v.tarih DESC, v.makina_no ASC
    """
    df = run_query(sql)
    if df.empty:
        st.info("Bu tarihlerde kapalı MAP vardiyası bulunamadı."); return

    # Kolon İsimlerini Düzenle
    rename_map = {
        'id': 'ID', 'tarih': 'Tarih', 'makina_no': 'Makina', 'vardiya_no': 'Vrd',
        'urun_adi': 'Ürün', 'uretim': 'Üretim (pk)', 'fire': 'Fire (pk)', 'fire_oran_pct': 'Fire %'
    }
    df = df.rename(columns=rename_map)
    
    st.dataframe(df, width="stretch", hide_index=True)
    
    with st.expander("🖨️ Detaylı Rapor Seçimi"):
        selected_id = st.selectbox("Raporu hazırlamak istediğiniz Vardiya ID", df['ID'].tolist())
        if st.button("📄 SEÇİLİ RAPORU ÜRET VE ÖNİZLE"):
             # v6.5.2: Doğrudan map_rapor_pdf entegrasyonu
             from ui.map_uretim.map_rapor_pdf import uret_is_raporu_html
             import json
             html_rapor = uret_is_raporu_html(engine, int(selected_id))
             if html_rapor:
                st.components.v1.html(html_rapor, height=600, scrolling=True)
