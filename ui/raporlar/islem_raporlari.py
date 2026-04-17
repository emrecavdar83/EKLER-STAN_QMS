import streamlit as st
import pandas as pd
import json
from datetime import datetime
from sqlalchemy import text
from logic.data_fetcher import run_query
from ui.raporlar.report_utils import (
    _rapor_excel_export, 
    _get_personnel_display_map, 
    _generate_base_html, 
    get_istanbul_time
)

def render_islem_gecmisi_tab(engine, modul_key, bas_tarih, bit_tarih):
    """
    Anayasa v6.5: Modül bazlı kurumsal işlem raporlama bileşeni.
    MAP ve Soğuk Oda raporlama standartlarını baz alır.
    """
    st.markdown(f"### 🔍 {modul_key.upper().replace('_', ' ')} İşlem Geçmişi")
    st.caption("Bu bölümde seçilen tarih aralığında bu modülde gerçekleştirilen tüm kullanıcı hareketleri listelenir.")

    # 1. Veri Çekme
    is_pg = engine.dialect.name == 'postgresql'
    sql = f"""
        SELECT zaman, islem_tipi, detay, modul, kullanici_id, detay_json, ip_adresi 
        FROM sistem_loglari 
        WHERE modul = :m AND zaman BETWEEN :b AND :e
        ORDER BY zaman DESC
    """
    params = {"m": modul_key, "b": f"{bas_tarih} 00:00:00", "e": f"{bit_tarih} 23:59:59"}
    
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params)

    if df.empty:
        st.info("💡 Bu modülde seçilen tarihlerde herhangi bir işlem kaydı bulunamadı."); return

    # 2. Ön İzleme ve Filtreleme
    df['zaman_fmt'] = pd.to_datetime(df['zaman']).dt.strftime('%d.%m.%Y %H:%M')
    p_map = _get_personnel_display_map(run_query, engine)
    
    # Kullanıcı ismini parse et (detay içindeki [user] kısmından veya kullanici_id'den)
    def parse_user(row):
        detay = row['detay']
        if detay.startswith("[") and "]" in detay:
            u = detay[1:detay.find("]")]
            return p_map.get(u, u)
        return "Bilinmiyor"

    df['ayarlar_kullanicilar'] = df.apply(parse_user, axis=1)
    
    # Görsel Tablo
    display_df = df[['zaman_fmt', 'islem_tipi', 'ayarlar_kullanicilar', 'detay', 'ip_adresi']].copy()
    display_df.columns = ["Zaman", "İşlem Tipi", "Personel", "İşlem Detayı", "IP Adresi"]
    
    st.dataframe(display_df, width="stretch", hide_index=True)

    # 3. İhracat Seçenekleri
    c1, c2 = st.columns(2)
    with c1:
        _rapor_excel_export(st, display_df, None, f"{modul_key}_Islem_Logu", bas_tarih, bit_tarih)
    
    with c2:
        if st.button("📄 Kurumsal İşlem Beyan Raporu (PDF)", width="stretch", type="primary"):
            _render_pdf_preview(df, modul_key, bas_tarih, bit_tarih, p_map)

def _render_pdf_preview(df, modul_key, bas_tarih, bit_tarih, p_map):
    """HTML/PDF Rapor önizlemesini render eder."""
    html = _hazirla_islem_html_raporu(df, modul_key, bas_tarih, bit_tarih, p_map)
    st.divider()
    st.subheader("📋 Rapor Önizleme")
    st.components.v1.html(html, height=800, scrolling=True)
    
    # Print script
    html_json = json.dumps(html)
    st.components.v1.html(f"""
        <script>
        function printReport() {{
            var w = window.open('', '_blank');
            w.document.write({html_json});
            w.document.close();
            setTimeout(function() {{ w.print(); }}, 500);
        }}
        </script>
        <button onclick="printReport()" style="width:100%; padding:10px; background:#8B0000; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">
            🖨️ Yazıcıya Gönder / PDF Kaydet
        </button>
    """, height=60)

def _generate_log_rows_html(df):
    """Log satırlarını HTML formatında üretir."""
    trs = ""
    for _, row in df.iterrows():
        islem = row['islem_tipi']
        row_clr = "#ffffff"
        if "HATA" in islem or "RED" in islem: row_clr = "#fff5f5"
        elif "EKLEME" in islem: row_clr = "#f5fff5"
        
        trs += f"""
            <tr style="background-color: {row_clr};">
                <td>{row['zaman_fmt']}</td>
                <td><span class="badge" style="border:1px solid #777;">{islem}</span></td>
                <td><b>{row['ayarlar_kullanicilar']}</b></td>
                <td>{row['detay']}</td>
                <td style="font-family:monospace; font-size:9px;">{row['ip_adresi']}</td>
            </tr>
        """
    return trs

def _generate_signatures_html(df):
    """Personel imzalarını üretir."""
    top_users = df['ayarlar_kullanicilar'].value_counts().head(3).index.tolist()
    signatures = ""
    for user in top_users:
        u_clean = user.split('(')[0].strip()
        signatures += f"""
            <div class="imza-kutu">
                <b>{u_clean}</b>
                <br>Dijital Kayıt Onayı<br>
                <small>{get_istanbul_time().year} QMS Audit</small>
            </div>
        """
    return signatures if signatures else '<div class="imza-kutu"><b>İlgili Personel</b><br><br>İmza</div>'

def _hazirla_islem_html_raporu(df, modul_key, bas_tarih, bit_tarih, p_map):
    """MAP Standartlarında İşlem Beyan Raporu hazırlar."""
    period = f"{bas_tarih} - {bit_tarih}"
    title = f"{modul_key.upper().replace('_', ' ')} İŞLEM BEYAN RAPORU"
    doc_no = f"EKL-MGT-R-LOG-{modul_key.upper()[:3]}"
    
    summary_cards = f"""
        <div class="ozet-kart toplam">Toplam İşlem: {len(df)}</div>
        <div class="ozet-kart onay">Aktif Personel: {df['ayarlar_kullanicilar'].nunique()}</div>
        <div class="ozet-kart">Modül: {modul_key}</div>
    """
    
    trs = _generate_log_rows_html(df)
    content = f"""
        <p style="font-style: italic;">Aşağıdaki tablo, belirtilen tarih aralığında sistem üzerinde gerçekleştirilen işlemleri göstermektedir.</p>
        <table>
            <thead>
                <tr>
                    <th style="width:120px;">Zaman</th>
                    <th style="width:100px;">İşlem</th>
                    <th style="width:150px;">Personel</th>
                    <th>Açıklama / Detay</th>
                    <th style="width:80px;">IP</th>
                </tr>
            </thead>
            <tbody>
                {trs}
            </tbody>
        </table>
    """
    
    signatures = _generate_signatures_html(df)
    return _generate_base_html(title, doc_no, period, summary_cards, content, signatures)
