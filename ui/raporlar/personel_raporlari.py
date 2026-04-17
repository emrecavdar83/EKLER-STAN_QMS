import streamlit as st
import pandas as pd
from datetime import datetime
import json

from logic.data_fetcher import run_query, get_all_sub_department_ids
from ui.raporlar.report_utils import _rapor_excel_export, _get_personnel_display_map, _generate_base_html
from ui.raporlar.islem_raporlari import render_islem_gecmisi_tab

def render_personel_sub_module(engine, bas_tarih, bit_tarih, matrix_filters):
    st.subheader("👥 Personel & Organizasyon Raporları")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🧼 Hijyen Kontrol Özeti",
        "📊 Organizasyon Şeması",
        "📅 Vardiya Çizelgesi PDF",
        "🔍 İşlem Geçmişi"
    ])
    
    with tab1:
        _render_hijyen_raporu(engine, bas_tarih, bit_tarih, matrix_filters)

    with tab2:
        _render_organizasyon_semasi(engine)

    with tab3:
        from ui.raporlar.vardiya_raporu_pdf import render_vardiya_pdf_raporu
        render_vardiya_pdf_raporu(engine, bas_tarih=bas_tarih,
                                  bit_tarih=bit_tarih, key_prefix="vpr_raporlar")

    with tab4:
        render_islem_gecmisi_tab(engine, "personel_hijyen", bas_tarih, bit_tarih)

def _render_hijyen_raporu(engine, bas_tarih, bit_tarih, matrix_filters=None):
    saha_id = matrix_filters.get("saha") if matrix_filters else 0
    dept_id = matrix_filters.get("dept") if matrix_filters else 0
    
    personel_filter = ""
    if saha_id > 0:
        personel_filter += f" AND (p.operasyonel_bolum_id = {saha_id})"
    if dept_id > 0:
        all_depts = get_all_sub_department_ids(dept_id)
        personel_filter += f" AND (p.departman_id IN ({','.join(map(str, all_depts))}))"

    sql = f"""
        SELECT h.* FROM hijyen_kontrol_kayitlari h 
        LEFT JOIN ayarlar_kullanicilar p ON h.personel = p.ad_soyad 
        WHERE h.tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}' {personel_filter}
    """
    df = run_query(sql)
    if df.empty:
        st.warning("⚠️ Bu kriterlere uygun kayıt bulunamadı."); return
    
    uygunsuzluk = df[df['durum'] != 'Sorun Yok']
    if not uygunsuzluk.empty:
        st.error(f"⚠️ {len(uygunsuzluk)} Uygunsuzluk / Devamsızlık")
        st.dataframe(uygunsuzluk, width="stretch", hide_index=True)
    else:
        st.success("✅ Tüm kayıtlar uygun bulundu.")
        
    p_map = _get_personnel_display_map(run_query, engine)
    for col in ['ayarlar_kullanicilar', 'kullanici']:
        if col in df.columns:
            df[col] = df[col].astype(str).map(lambda x: p_map.get(x, x))

    with st.expander("📋 Detaylı Kayıt Listesi", expanded=True):
        st.dataframe(df, width="stretch", hide_index=True)
    
    _rapor_excel_export(st, df, None, "Personel_Hijyen_Raporu", bas_tarih, bit_tarih)

    # HTML/PDF Generation
    toplam_pers = len(df)
    uygun_pers = len(df[df['durum'] == 'Sorun Yok'])
    red_pers = toplam_pers - uygun_pers
    
    cards = f"""
      <div class="ozet-kart toplam">Kontrol Edilen Personel: {toplam_pers}</div>
      <div class="ozet-kart onay">Uygun: {uygun_pers}</div>
      <div class="ozet-kart red">Uygunsuz / Kusurlu: {red_pers}</div>
    """
    
    trs = ""
    for _, r in df.iterrows():
        dur = str(r.get('durum',''))
        badge = f'<span class="badge bg-green">Sorun Yok</span>' if dur == 'Sorun Yok' else f'<span class="badge bg-red">{dur}</span>'
        trs += f"<tr><td>{r.get('saat','')}</td><td>{r.get('bolum','')}</td><td>{r.get('ayarlar_kullanicilar','')}</td><td>{r.get('vardiya','')}</td><td>{badge}</td><td>{r.get('aksiyon','-')}</td><td>{r.get('kullanici','')}</td></tr>"
        
    content = f"<table><thead><tr><th>Saat</th><th>Bölüm</th><th>Personel</th><th>Vardiya</th><th>Durum</th><th>Aksiyon</th><th>Kontrolör</th></tr></thead><tbody>{trs}</tbody></table>"
    sigs = """
        <div class="imza-kutu"><b>Kontrolü Yapan</b><br><br>İmza</div>
        <div class="imza-kutu"><b>Vardiya Amiri</b><br><br>İmza</div>
        <div class="imza-kutu"><b>Kalite Yönetimi</b><br><br>İmza</div>
    """
    html_rapor = _generate_base_html("PERSONEL HİJYEN KONTROL RAPORU", "EKL-KYS-HIJ-002", f"{bas_tarih} - {bit_tarih}", cards, content, sigs)
    
    html_json = json.dumps(html_rapor)
    pdf_js = f"<script>function p(){{var w=window.open('','_blank');w.document.write({html_json});w.document.close();setTimeout(function(){{w.print();}},600);}}</script><button onclick='p()' style='width:100%;padding:10px;background:#8B0000;color:white;border:none;border-radius:5px;cursor:pointer;'>🖨️ PDF Kaydet</button>"
    st.components.v1.html(pdf_js, height=60)

def _render_organizasyon_semasi(engine):
    st.info("📊 Organizasyon şeması QMS departman hiyerarşisi üzerinden dinamik olarak oluşturulur.")
    from logic.data_fetcher import get_qms_department_tree
    tree = get_qms_department_tree()
    if tree:
        for item in tree:
            st.markdown(f"• {item}")
    else:
        st.warning("Henüz hiyerarşi tanımlanmamış.")
