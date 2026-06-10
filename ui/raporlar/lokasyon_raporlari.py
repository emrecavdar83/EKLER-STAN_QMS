import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import time

from logic.data_fetcher import run_query
from ui.raporlar.report_utils import _generate_base_html

def render_lokasyon_sub_module(engine):
    st.subheader("📍 Lokasyon & Envanter Raporları")
    
    tab1, tab2 = st.tabs(["🗺️ Lokasyon Envanter Haritası", "🖼️ Görsel Fabrika Şeması"])
    
    with tab1:
        _render_lokasyon_envanter_raporu(engine)
    
    with tab2:
        _render_lokasyon_haritasi(engine)

def _render_lokasyon_envanter_raporu(engine):
    st.info("📍 Kurumsal Lokasyon & Proses Haritası (Hiyerarşik)")
    
    df = run_query("SELECT id, ad, tip, parent_id, sorumlu_id, sira_no, aktif, created_at, sorumlu_departman, guncelleme_tarihi FROM lokasyonlar WHERE aktif = 1")
    if df.empty:
        st.warning("Gösterilecek bir lokasyon veya ekipman tanımı yok."); return
        
    st.dataframe(df, width="stretch", hide_index=True)
    
    if st.button("🖨️ Envanter PDF Raporu Oluştur"):
        # Özet kartlar
        toplam = len(df)
        tip_sayilari = df['tip'].value_counts().to_dict() if 'tip' in df.columns else {}
        tip_ozet = " | ".join([f"{k}: {v}" for k, v in tip_sayilari.items()]) if tip_sayilari else "-"

        cards = f"""
          <div class="ozet-kart toplam">Toplam Lokasyon / Ekipman: {toplam}</div>
          <div class="ozet-kart onay">Aktif Kayıt: {toplam}</div>
          <div class="ozet-kart" style="background:#fff8e1;color:#f57f17;border:1px solid #f57f17;">Tip Dağılımı: {tip_ozet}</div>
        """

        # Tablo satırları
        trs = ""
        for _, r in df.iterrows():
            parent = str(r.get('parent_id', '-')) if pd.notna(r.get('parent_id')) else '-'
            sorumlu = str(r.get('sorumlu_departman', '-')) if pd.notna(r.get('sorumlu_departman')) else '-'
            created = str(r.get('created_at', ''))[:10] if pd.notna(r.get('created_at')) else '-'
            trs += (
                f"<tr>"
                f"<td>{r.get('id','')}</td>"
                f"<td><b>{r.get('ad','')}</b></td>"
                f"<td>{r.get('tip','')}</td>"
                f"<td>{parent}</td>"
                f"<td>{sorumlu}</td>"
                f"<td>{created}</td>"
                f"</tr>"
            )

        content = (
            "<table><thead><tr>"
            "<th>ID</th><th>Ad</th><th>Tip</th><th>Üst Lokasyon</th><th>Sorumlu Departman</th><th>Kayıt Tarihi</th>"
            f"</tr></thead><tbody>{trs}</tbody></table>"
        )

        sigs = """
            <div class="imza-kutu"><b>Tesis Yöneticisi</b><br><br>İmza</div>
            <div class="imza-kutu"><b>Kalite Güvence</b><br><br>İmza</div>
            <div class="imza-kutu"><b>Genel Müdür</b><br><br>İmza</div>
        """

        bugun = str(date.today())
        html_rapor = _generate_base_html(
            "LOKASYON & ENVANTER RAPORU",
            "EKL-KYS-LOK-001",
            bugun,
            cards,
            content,
            sigs
        )

        html_json = json.dumps(html_rapor)
        pdf_js = (
            f"<script>function p(){{var w=window.open('','_blank');w.document.write({html_json});w.document.close();setTimeout(function(){{w.print();}},600);}}</script>"
            f"<button onclick='p()' style='width:100%;padding:10px;background:#8B0000;color:white;border:none;border-radius:5px;cursor:pointer;'>🖨️ PDF Kaydet / Yazdır</button>"
        )
        st.components.v1.html(pdf_js, height=60)

def _render_lokasyon_haritasi(engine):
    st.write("### 🖼️ Fabrika Görsel Yerleşim Şeması")
    st.caption("v5.0: Dinamik SVG/Canvas tabanlı yerleşim planı.")
    # Placeholder for visual map
    st.image("https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png", width=200)
    st.warning("Görsel şema veritabanı koordinatları üzerinden dinamik olarak oluşturulacaktır.")
