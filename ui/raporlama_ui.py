import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta, date
import io
import time, pytz, os
import plotly.express as px

from database.connection import get_engine
from logic.data_fetcher import (
    run_query, veri_getir, get_user_roles,
    get_all_sub_department_ids, get_personnel_hierarchy,
    get_department_options_hierarchical
)
from logic.auth_logic import kullanici_yetkisi_var_mi
from constants import (
    VARDIYA_LISTESI,
    get_position_name,
    get_position_icon,
    get_position_color
)
from soguk_oda_utils import get_matrix_data, get_trend_data

engine = get_engine()

# --- HELPERS ---

def _get_personnel_display_map(engine):
    """
    Kullanici_adi -> 'Ad Soyad (Görev) [Saha]' eşleşmesini döndürür.
    Anayasa Madde 4: Dinamik veri çekme ve Matris Kimliği.
    """
    try:
        query = """
            SELECT p.kullanici_adi, p.ad_soyad, p.gorev, b.ad as saha_adi
            FROM personel p
            LEFT JOIN qms_departmanlar b ON p.operasyonel_bolum_id = b.id
            WHERE p.kullanici_adi IS NOT NULL
        """
        df_p = run_query(query)
        if df_p.empty: return {}
        
        df_p.columns = [c.lower() for c in df_p.columns]
        
        def format_name(row):
            base = str(row.get('ad_soyad', row.get('kullanici_adi', '-')))
            if base in ('None', 'nan', '', '-'): base = str(row.get('kullanici_adi', '-'))
            gorev = str(row.get('gorev', ''))
            saha = str(row.get('saha_adi', ''))
            
            display = base
            if gorev and gorev not in ('nan', 'None', ''):
                display += f" ({gorev})"
            if saha and saha not in ('nan', 'None', ''):
                display += f" [{saha}]"
            return display
            
        res_map = dict(zip(df_p['kullanici_adi'].astype(str), df_p.apply(format_name, axis=1)))
        return {k: v for k, v in res_map.items() if k not in ('None', 'nan')}
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="RAPOR_PERSONEL_MAP", tip="UI")
        return {}

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

# --- HELPERS ---

def _rapor_excel_export(df_main, df_summary=None, report_name="Rapor", start_date=None, end_date=None):
    """
    Merkezi Excel İhracat Fonksiyonu.
    Anayasa Madde 7 Uyarınca: Standart Dosya İsimlendirmesi ve Çoklu Tablo Desteği.
    """
    try:
        # İndirme Tarihi (Bugün)
        download_tarih = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%Y%m%d')
        
        # Dosya İsim Standardı: RAPOR_ADI_BAS_BIT_INDIRMETARIHI
        safe_name = report_name.replace(' ', '_').replace('/', '-').upper()
        start_str = str(start_date).replace('-', '') if start_date else ""
        end_str = str(end_date).replace('-', '') if end_date else ""
        file_name = f"{safe_name}_{start_str}_{end_str}_{download_tarih}.xlsx"

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Ana Veri
            df_main.to_excel(writer, index=False, sheet_name='Kayıtlar')
            # Varsa Özet Veri
            if df_summary is not None and not df_summary.empty:
                df_summary.to_excel(writer, index=False, sheet_name='Özet')
                
        excel_data = output.getvalue()
        st.download_button(
            label=f"📥 Excel ({report_name}) İndir",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"dl_{safe_name}_{time.time()}"
        )
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="RAPOR_EXCEL", tip="UI")
        st.caption("ℹ️ İpucu: openpyxl kütüphanesinin yüklü olduğundan emin olun.")

# --- HTML BASE GENERATOR ---
def _generate_base_html(title, doc_no, period, summary_cards, content, signatures):
    rapor_tarihi = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%d.%m.%Y %H:%M')
    LOGO_URL = "https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png"
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 0; }}
  @media print {{ 
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; margin: 15mm; }}
    .no-print {{ display: none; }}
  }}
  body {{ font-family: Arial, sans-serif; font-size: 11px; color: #333; background: white; margin: 0; padding: 15mm; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #8B0000; padding-bottom: 10px; margin-bottom: 14px; }}
  .header-logo img {{ height: 50px; }}
  .header-title {{ text-align: center; }}
  .header-title h1 {{ font-size: 16px; color: #1a2744; margin: 0; }}
  .header-title p {{ margin: 2px 0; font-size: 11px; color: #555; }}
  .header-meta {{ text-align: right; font-size: 10px; color: #555; }}
  .ozet-bar {{ display: flex; gap: 12px; margin-bottom: 14px; width: 100%; }}
  .ozet-kart {{ flex: 1; padding: 6px 12px; border-radius: 4px; text-align: center; font-weight: bold; font-size: 12px; }}
  .onay {{ background: #e8f5e9; color: #2e7d32; border: 1px solid #2e7d32; }}
  .red {{ background: #ffebee; color: #b71c1c; border: 1px solid #b71c1c; }}
  .toplam {{ background: #e3f2fd; color: #1565c0; border: 1px solid #1565c0; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; }}
  th {{ background-color: #1a2744; color: white; padding: 6px; text-align: left; border: 1px solid #ccc; }}
  td {{ padding: 6px; border: 1px solid #ccc; }}
  tr:nth-child(even) {{ background-color: #f8f8f8; }}
  .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: bold; display: inline-block; text-align: center; }}
  .bg-green {{ background-color: #2e7d32; color: white; }}
  .bg-red {{ background-color: #b71c1c; color: white; }}
  .imza-alani {{ margin-top: 30px; border-top: 2px solid #1a2744; padding-top: 15px; page-break-inside: avoid; }}
  .imza-tablo {{ display: flex; gap: 20px; }}
  .imza-kutu {{ flex: 1; border: 1px solid #bbb; border-radius: 4px; padding: 10px 10px 40px 10px; text-align: center; font-size: 10px; color: #555; background: #fafafa; }}
  .imza-kutu b {{ display: block; color: #1a2744; margin-bottom: 8px; font-size: 11px; }}
  .footer {{ margin-top: 20px; border-top: 1px solid #ccc; padding-top: 8px; display: flex; justify-content: space-between; font-size: 9px; color: #777; }}
  .brc-warning {{ font-weight: bold; color: #b71c1c; font-size: 10px; text-align: center; margin-bottom: 5px; }}
</style>
</head>
<body>
<div class="header">
  <div class="header-logo"><img src="{LOGO_URL}" alt="Logo"></div>
  <div class="header-title">
    <h1>{title}</h1>
    <p>Doküman No: {doc_no}</p>
    <p>Dönem: <b>{period}</b></p>
  </div>
  <div class="header-meta">Sayfa: 1 / 1<br>Rev:02 - 15.01.2026<br>Baskı Tarihi: <b>{rapor_tarihi}</b></div>
</div>
<div class="ozet-bar">
  {summary_cards}
</div>
{content}
<div class="imza-alani">
  <div class="brc-warning">UYARI: Kritik sapma veya uygunsuzluk durumunda derhal Kalite Güvence birimine haber veriniz.</div>
  <div class="imza-tablo">
    {signatures}
  </div>
</div>
<div class="footer">
  <span>Gizlilik: Dahili Kullanım (BRCGS v9 Uyumlu Form)</span>
  <span>Ekleristan Kalite Yönetim Sistemi v2.0</span>
  <span>Baskı: {rapor_tarihi}</span>
</div>
</body>
</html>
"""

# --- MODÜL 1: ÜRETİM VE VERİMLİLİK ---
def _render_uretim_raporu(bas_tarih, bit_tarih, matrix_filters=None):
    # Matris Filtre Hazırlığı
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
        st.warning("Bu kriterlere uygun üretim kaydı bulunamadı.")
        return
    df.columns = [c.lower() for c in df.columns]

    k1, k2, k3 = st.columns(3)
    k1.metric("Toplam Üretim (Adet)", f"{df['miktar'].sum():,}")
    k2.metric("Toplam Fire", f"{df['fire'].sum():,}")
    fire_oran = (df['fire'].sum() / df['miktar'].sum()) * 100 if df['miktar'].sum() > 0 else 0
    k3.metric("Ortalama Fire Oranı", f"%{fire_oran:.2f}")

    st.subheader("📦 Ürün Bazında Özet")
    urun_ozet = df.groupby('urun').agg({'miktar': 'sum', 'fire': 'sum', 'lot_no': 'count'}).reset_index()
    urun_ozet.columns = ['Ürün Adı', 'Toplam Üretim', 'Toplam Fire', 'Lot Sayısı']
    urun_ozet['Fire Oranı (%)'] = (urun_ozet['Toplam Fire'] / urun_ozet['Toplam Üretim'] * 100).round(2)
    st.dataframe(urun_ozet.sort_values('Toplam Üretim', ascending=False), use_container_width=True, hide_index=True)

    st.subheader("📋 Detaylı Kayıtlar")
    cols = ['tarih', 'saat', 'vardiya', 'urun', 'lot_no', 'miktar', 'fire', 'kullanici', 'notlar']
    df_display = df[[c for c in cols if c in df.columns]].copy()
    
    # Personel Mapping Uygula
    p_map = _get_personnel_display_map(engine)
    if 'kullanici' in df_display.columns:
        df_display['kullanici'] = df_display['kullanici'].astype(str).map(lambda x: p_map.get(x, x))
    
    rename_map = {'tarih': 'Tarih', 'saat': 'Saat', 'vardiya': 'Vardiya', 'urun': 'Ürün Adı', 'lot_no': 'Lot No', 'miktar': 'Miktar', 'fire': 'Fire', 'kullanici': 'Uygulayıcı (Sorumlu)', 'notlar': 'Notlar'}
    df_display.columns = [rename_map.get(c, c) for c in df_display.columns]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    col_excel, col_pdf = st.columns(2)
    with col_excel:
        _rapor_excel_export(df_display, urun_ozet, "Üretim_Raporu", bas_tarih, bit_tarih)
    
    # HTML RAPORU OLUŞTUR
    toplam_uretim = df['miktar'].sum()
    cards = f"""
      <div class="ozet-kart toplam">Toplam Üretim: {toplam_uretim:,} Adet</div>
      <div class="ozet-kart onay">Ortalama Fire Oranı: %{fire_oran:.2f}</div>
      <div class="ozet-kart red">Toplam Fire: {df['fire'].sum():,} Adet</div>
    """
    
    trs = ""
    for _, r in df_display.iterrows():
        f_badge = f'<span class="badge bg-green">ONAY</span>' if float(r.get('Fire', 0)) <= 50 else f'<span class="badge bg-red">KRİTİK FİRE</span>'
        trs += f"<tr><td>{r.get('Saat','')}</td><td>{r.get('Vardiya','')}</td><td>{r.get('Ürün Adı','')}</td><td>{r.get('Lot No','')}</td><td>{r.get('Miktar','')}</td><td>{r.get('Fire','')}</td><td>{r.get('Notlar','')}</td><td>{f_badge}</td><td>{r.get('Uygulayıcı (Sorumlu)','')}</td></tr>"
        
    content = f"""
    <table>
      <thead>
        <tr><th>Saat</th><th>Vardiya</th><th>Ürün</th><th>Parti (Lot) No</th><th>Üretim</th><th>Fire</th><th>Fire Sebebi</th><th>Durum</th><th>Sorumlu Personel</th></tr>
      </thead>
      <tbody>{trs}</tbody>
    </table>
    """
    sigs = """
        <div class="imza-kutu"><b>Üretim Sorumlusu</b><br>Ad Soyad / İmza</div>
        <div class="imza-kutu"><b>Vardiya Şefi</b><br>Ad Soyad / İmza</div>
        <div class="imza-kutu"><b>Üretim Müdürü</b><br>Ad Soyad / İmza</div>
    """
    html_rapor = _generate_base_html("GÜNLÜK ÜRETİM VE FİRE BEYAN RAPORU", "EKL-URE-001", f"{bas_tarih} / {bit_tarih}", cards, content, sigs)
    
    import json as _json
    html_json = _json.dumps(html_rapor)
    pdf_js = f"""
    <script>
    function printUretimReport() {{
        var html = {html_json};
        var blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
        var url = URL.createObjectURL(blob);
        var win = window.open(url, '_blank');
        win.addEventListener('load', function() {{ setTimeout(function() {{ win.print(); }}, 600); }});
    }}
    </script>
    <button onclick="printUretimReport()" style="width:100%; padding:10px 0; background:#8B0000; color:white; border:none; border-radius:5px; font-size:14px; font-weight:bold; cursor:pointer;">
        🖨️ Yazdır / PDF Kaydet
    </button>
    """
    with col_pdf:
        st.components.v1.html(pdf_js, height=55)

# --- MODÜL 2: KALİTE (KPI) ANALİZİ ---
def _kpi_html_raporu_olustur(df_urun, urun_sec, bas_tarih, bit_tarih, personel_map):
    """KPI icin A4 formatli, kurumsal kimlige uygun HTML rapor dondurur."""
    import re, os
    rapor_tarihi = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%d.%m.%Y %H:%M')
    LOGO_URL = "https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png"

    satir_html = ""
    for _, row in df_urun.iterrows():
        notlar = str(row.get('notlar', ''))
        karar = str(row.get('karar', '-'))
        karar_renk = "#2e7d32" if karar == "ONAY" else "#b71c1c"
        karar_ikon = "ONAYLANDI" if karar == "ONAY" else "REDDEDILDI"
        kayit_saati = str(row.get('saat', '-'))
        kullanici_adi = str(row.get('kullanici', str(row.get('kaydeden', '-'))))
        tam_ad = personel_map.get(kullanici_adi, kullanici_adi)
        vardiya = str(row.get('vardiya', '-'))
        tat = str(row.get('tat', '-'))
        goruntu = str(row.get('goruntu', '-'))
        lot = str(row.get('lot_no', row.get('lot_tlar', '-')))
        stt = str(row.get('stt_tarihi', '-'))
        numune_adet = int(float(row.get('numune_sayisi', 1) or 1))

        olcum_satirlari = ""
        matches = re.findall(r'\[N(\d+): ([^\]]+)\]', notlar)
        if matches:
            for idx, (num, vals) in enumerate(matches):
                bg = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
                olcum_satirlari += f"<tr style='background:{bg}'><td style='padding:5px 8px;border:1px solid #ddd;text-align:center'>N{num}</td>"
                params = [v.strip() for v in vals.split(',')]
                for p in params:
                    parts = p.split('=')
                    val = parts[1].strip() if len(parts) == 2 else p
                    olcum_satirlari += f"<td style='padding:5px 8px;border:1px solid #ddd;text-align:center'>{val}</td>"
                olcum_satirlari += "</tr>"
        else:
            avg1 = round(float(row.get('olcum1_ort', 0) or 0), 2)
            avg2 = round(float(row.get('olcum2_ort', 0) or 0), 2)
            avg3 = round(float(row.get('olcum3_ort', 0) or 0), 2)
            olcum_satirlari = f"<tr><td style='padding:5px 8px;border:1px solid #ddd;text-align:center'>Ort.</td><td style='padding:5px 8px;border:1px solid #ddd;text-align:center'>{avg1}</td><td style='padding:5px 8px;border:1px solid #ddd;text-align:center'>{avg2}</td><td style='padding:5px 8px;border:1px solid #ddd;text-align:center'>{avg3}</td></tr>"

        foto_html = ""
        foto_adi = str(row.get('fotograf_yolu', ''))
        if foto_adi and foto_adi not in ('nan', '', 'None'):
            foto_yolu = os.path.join('data', 'uploads', 'kpi', foto_adi)
            if os.path.exists(foto_yolu):
                import base64 as b64lib
                ext = foto_adi.split('.')[-1].lower()
                mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else 'image/png'
                with open(foto_yolu, 'rb') as f:
                    foto_b64 = b64lib.b64encode(f.read()).decode()
                foto_html = f'<p><b>STT Etiket Fotografı:</b></p><img src="data:{mime};base64,{foto_b64}" style="max-width:180px;max-height:180px;border:1px solid #ddd;border-radius:4px;margin-top:6px">'
            else:
                foto_html = '<p style="color:#999;font-style:italic;font-size:11px">Fotograf kaydi var ancak sunucuda bulunamadi.</p>'

        karar_ok = "OK" if tat == "Uygun" else "UYGUNSUZ"
        goruntu_ok = "OK" if goruntu == "Uygun" else "UYGUNSUZ"

        satir_html += f"""
        <div class="kayit-kart">
            <div class="kayit-baslik" style="background:{karar_renk};">
                <span>{row.get('tarih','')} / {kayit_saati} | Vardiya: {vardiya} | Lot: {lot}</span>
                <span class="karar-badge">{karar_ikon}</span>
            </div>
            <div class="kayit-icerik">
                <div class="iki-kolon">
                    <div>
                        <p><b>Urun:</b> {urun_sec}</p>
                        <p><b>Lot No:</b> {lot}</p>
                        <p><b>STT Tarihi:</b> {stt}</p>
                        <p><b>Numune Sayisi:</b> {numune_adet}</p>
                        <p><b>Tat / Koku:</b> {karar_ok} ({tat})</p>
                        <p><b>Goruntusu / Renk:</b> {goruntu_ok} ({goruntu})</p>
                    </div>
                    <div>
                        <p><b>Kaydeden Personel:</b> <u>{tam_ad}</u></p>
                        <p style="font-size:10px;color:#777">Kullanici: {kullanici_adi}</p>
                        <p><b>Kalite Notu:</b> {notlar[:300] if notlar else '-'}</p>
                        {foto_html}
                    </div>
                </div>
                <table style="width:100%;border-collapse:collapse;margin-top:10px;font-size:12px">
                    <thead><tr style="background:#1a2744;color:white">
                        <th style="padding:6px 8px;border:1px solid #ddd">Numune</th>
                        <th style="padding:6px 8px;border:1px solid #ddd">Olcum 1</th>
                        <th style="padding:6px 8px;border:1px solid #ddd">Olcum 2</th>
                        <th style="padding:6px 8px;border:1px solid #ddd">Olcum 3</th>
                    </tr></thead>
                    <tbody>{olcum_satirlari}</tbody>
                </table>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: A4; margin: 18mm 15mm 18mm 15mm; }}
  @media print {{
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .kayit-kart {{ page-break-inside: avoid; }}
  }}
  body {{ font-family: Arial, sans-serif; font-size: 12px; color: #222; background: white; margin: 0; padding: 10px; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #8B0000; padding-bottom: 10px; margin-bottom: 14px; }}
  .header-logo img {{ height: 48px; }}
  .header-title {{ text-align: center; }}
  .header-title h1 {{ font-size: 18px; color: #1a2744; margin: 0; }}
  .header-title p {{ margin: 2px 0; font-size: 11px; color: #555; }}
  .header-meta {{ text-align: right; font-size: 10px; color: #555; }}
  .ozet-bar {{ display: flex; gap: 12px; margin-bottom: 14px; }}
  .ozet-kart {{ flex: 1; padding: 8px 12px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 13px; }}
  .onay {{ background: #e8f5e9; color: #2e7d32; border: 1.5px solid #2e7d32; }}
  .red {{ background: #ffebee; color: #b71c1c; border: 1.5px solid #b71c1c; }}
  .toplam {{ background: #e3f2fd; color: #1565c0; border: 1.5px solid #1565c0; }}
  .filtre-baslik {{ background: #1a2744; color: white; padding: 6px 12px; border-radius: 4px; font-size: 13px; margin-bottom: 14px; }}
  .kayit-kart {{ border: 1px solid #ddd; border-radius: 5px; margin-bottom: 14px; overflow: hidden; }}
  .kayit-baslik {{ color: white; padding: 7px 12px; font-weight: bold; font-size: 12px; display: flex; justify-content: space-between; }}
  .karar-badge {{ background: rgba(255,255,255,0.25); padding: 2px 8px; border-radius: 10px; font-size: 11px; }}
  .kayit-icerik {{ padding: 12px; }}
  .iki-kolon {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 8px; }}
  .iki-kolon p {{ margin: 3px 0; }}
  .imza-alani {{ margin-top: 24px; border-top: 2px solid #1a2744; padding-top: 12px; }}
  .imza-alani h3 {{ color: #1a2744; font-size: 13px; margin-bottom: 10px; }}
  .imza-tablo {{ display: flex; gap: 20px; }}
  .imza-kutu {{ flex: 1; border: 1px solid #bbb; border-radius: 4px; padding: 10px; min-height: 60px; text-align: center; font-size: 11px; color: #555; }}
  .imza-kutu b {{ display: block; color: #1a2744; margin-bottom: 6px; }}
  .footer {{ margin-top: 20px; border-top: 1px solid #ccc; padding-top: 8px; display: flex; justify-content: space-between; font-size: 10px; color: #777; }}
</style>
</head>
<body>
<div class="header">
  <div class="header-logo"><img src="{LOGO_URL}" alt="Ekleristan Logo"></div>
  <div class="header-title">
    <h1>KALİTE KONTROL ANALİZ RAPORU</h1>
    <p>Ürün Bazlı Ölçüm Kaydı &nbsp;|&nbsp; EKL-KYS-KPI-001</p>
    <p>Dönem: {str(bas_tarih)} / {str(bit_tarih)} &nbsp;|&nbsp; Ürün: <b>{urun_sec}</b></p>
  </div>
  <div class="header-meta">Rapor Tarihi:<br><b>{rapor_tarihi}</b></div>
</div>

<div class="ozet-bar">
  <div class="ozet-kart onay">Onaylanan: {len(df_urun[df_urun['karar']=='ONAY'])}</div>
  <div class="ozet-kart red">Reddedilen: {len(df_urun[df_urun['karar']=='RED'])}</div>
  <div class="ozet-kart toplam">Toplam Analiz: {len(df_urun)}</div>
</div>

<div class="filtre-baslik">Tüm Kayıtlar -- {urun_sec}</div>
{satir_html}

<div class="imza-alani">
  <h3>İmza ve Onay Alanı</h3>
  <div class="imza-tablo">
    <div class="imza-kutu"><b>Kalite Kontrol Personeli</b>___________________<br>Ad Soyad / İmza / Tarih</div>
    <div class="imza-kutu"><b>Vardiya Şefi</b>___________________<br>Ad Soyad / İmza / Tarih</div>
    <div class="imza-kutu"><b>Kalite Müdürü</b>___________________<br>Ad Soyad / İmza / Tarih</div>
  </div>
</div>

<div class="footer">
  <span>Gizlilik: Dahili Kullanım</span>
  <span>Ekleristan Kalite Yönetim Sistemi v2.0</span>
  <span>Rapor: {rapor_tarihi}</span>
</div>
</body>
</html>"""
    return html


def _render_kpi_raporu(bas_tarih, bit_tarih):
    """Ürün bazlı KPI raporu: ölçüm detayları, personel tam adı, imza, Excel + PDF."""
    import json as _json
    df = run_query(f"SELECT id, tarih, urun_adi, miktar, karar, personel_id, olcumler_json FROM urun_kpi_kontrol WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("Bu tarih aralığında kalite kaydı bulunamadı.")
        return

    df.columns = [c.lower() for c in df.columns]

    personel_map = _get_personnel_display_map(engine)

    onay_s = len(df[df['karar'] == 'ONAY'])
    red_s  = len(df[df['karar'] == 'RED'])
    k1, k2, k3 = st.columns(3)
    k1.success(f"Onaylanan: {onay_s}")
    k2.error(f"Reddedilen: {red_s}")
    k3.info(f"Toplam: {len(df)}")

    st.divider()

    urunler = sorted(df['urun'].dropna().unique().tolist())
    urun_sec = st.selectbox("Ürün Seçin", ["(Tümü)"] + urunler)
    df_urun = df if urun_sec == "(Tümü)" else df[df['urun'] == urun_sec]

    if df_urun.empty:
        st.info("Seçilen ürün için kayıt yok.")
        return

    with st.expander(f"{urun_sec} -- {len(df_urun)} Kayıt (önizleme)", expanded=True):
        goruntu_cols = ['tarih', 'saat', 'vardiya', 'urun',
                        'lot_no' if 'lot_no' in df_urun.columns else 'lot_tlar',
                        'numune_sayisi', 'tat', 'goruntu', 'karar', 'kullanici']
        goruntu_cols = [c for c in goruntu_cols if c in df_urun.columns]
        st.dataframe(df_urun[goruntu_cols], use_container_width=True, hide_index=True)

    st.divider()
    col_excel, col_pdf = st.columns(2)

    with col_excel:
        _rapor_excel_export(df_urun, None, f"KPI_{urun_sec}", bas_tarih, bit_tarih)

    html_rapor = _kpi_html_raporu_olustur(df_urun, urun_sec, bas_tarih, bit_tarih, personel_map)
    html_json = _json.dumps(html_rapor)
    pdf_js = f"""
    <script>
    function printKPIReport() {{
        var html = {html_json};
        var blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
        var url = URL.createObjectURL(blob);
        var win = window.open(url, '_blank');
        win.addEventListener('load', function() {{
            setTimeout(function() {{ win.print(); }}, 600);
        }});
    }}
    </script>
    <button onclick="printKPIReport()" style="
        width:100%; padding:10px 0; background:#8B0000; color:white;
        border:none; border-radius:5px; font-size:14px; font-weight:bold;
        cursor:pointer;">
        🖨️ Yazdır / PDF Kaydet
    </button>
    """
    with col_pdf:
        st.components.v1.html(pdf_js, height=55)


# --- MODÜL 3: GÜNLÜK OPERASYONEL RAPOR ---
def _render_gunluk_operasyonel_rapor(bas_tarih, matrix_filters=None):
    """
    📅 Günlük Operasyonel Rapor: Yönetici Özeti, Kritik Sapmalar ve Kurumsal PDF Çıktısı.
    Anayasa v3.2: Matris izolasyonu eklendi.
    """
    st.info(f"📅 **{bas_tarih}** tarihli operasyonel performans ve kontrol özeti.")
    t_str = str(bas_tarih)
    
    # Matris Filtre Hazırlığı
    saha_id = matrix_filters.get("saha") if matrix_filters else 0
    dept_id = matrix_filters.get("dept") if matrix_filters else 0
    
    personel_filter = ""
    if saha_id > 0:
        personel_filter += f" AND (p.operasyonel_bolum_id = {saha_id})"
    if dept_id > 0:
        # Alt departmanları da dahil et
        all_depts = get_all_sub_department_ids(dept_id)
        personel_filter += f" AND (p.departman_id IN ({','.join(map(str, all_depts))}))"

    # Veri Çekme (Matris Uyumlu)
    kpi_sql = f"""
        SELECT k.* FROM urun_kpi_kontrol k 
        LEFT JOIN personel p ON k.kullanici = p.kullanici_adi 
        WHERE k.tarih='{t_str}' {personel_filter}
    """
    kpi_df = run_query(kpi_sql)
    
    # Üretim filtrelemesi (Uygulayıcı bazlı)
    uretim_sql = f"""
        SELECT d.* FROM depo_giris_kayitlari d 
        LEFT JOIN personel p ON d.kullanici = p.kullanici_adi 
        WHERE d.tarih='{t_str}' {personel_filter}
    """
    uretim_df = run_query(uretim_sql)
    
    # Hijyen filtrelemesi
    hijyen_sql = f"""
        SELECT h.* FROM hijyen_kontrol_kayitlari h 
        LEFT JOIN personel p ON h.personel = p.ad_soyad 
        WHERE h.tarih='{t_str}' {personel_filter.replace('p.kullanici_adi', 'p.ad_soyad')}
    """
    # Not: Hijyende hem denetlenen hem denetleyen var, biz denetlenen personel üzerinden süzüyoruz.
    hijyen_df = run_query(hijyen_sql)
    
    temizlik_df = run_query(f"SELECT * FROM temizlik_kayitlari WHERE tarih='{t_str}'")

    sosts_query = f"""
        SELECT o.id as oda_id, o.oda_adi, m.sicaklik_degeri, m.sapma_var_mi, m.olcum_zamani, m.kaydeden_kullanici 
        FROM sicaklik_olcumleri m 
        JOIN soguk_odalar o ON m.oda_id = o.id 
        WHERE {"DATE(m.olcum_zamani)" if "sqlite" in str(engine.url) else "m.olcum_zamani::date"} = '{t_str}'
    """
    sosts_df = run_query(sosts_query)

    # Özet Metrikler
    red_s = len(kpi_df[kpi_df['karar'] == 'RED']) if not kpi_df.empty else 0
    uyg_h = len(hijyen_df[hijyen_df['durum'] != 'Sorun Yok']) if not hijyen_df.empty else 0
    sapma_s = len(sosts_df[sosts_df['sapma_var_mi'] == 1]) if not sosts_df.empty else 0
    toplam_uretim = uretim_df['miktar'].sum() if not uretim_df.empty else 0

    # UI Metrik Kartları
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Üretim", f"{toplam_uretim:,} Adet")
    m2.metric("KPI Red", red_s, delta=red_s, delta_color="inverse")
    m3.metric("Hijyen Kusur", uyg_h, delta=uyg_h, delta_color="inverse")
    m4.metric("Oda Sapma", sapma_s, delta=sapma_s, delta_color="inverse")

    if (red_s + uyg_h + sapma_s) > 0:
        st.error(f"🚨 KRİTİK BİLGİ: Bugün {red_s + uyg_h + sapma_s} adet uygunsuzluk tespit edildi.")
    else:
        st.success("✅ Tüm operasyonel süreçler bugün sorunsuz tamamlandı.")

    # Detaylı Tablolar (Expanders)
    with st.expander("🔍 Detaylı Akış Tabloları", expanded=False):
        if not kpi_df.empty: st.write("**KPI:**", kpi_df)
        if not uretim_df.empty: st.write("**Üretim:**", uretim_df)
        if not sosts_df.empty: st.write("**Soğuk Oda:**", sosts_df)
        if not hijyen_df.empty: st.write("**Hijyen:**", hijyen_df)

    st.divider()
    col_ex, col_pdf = st.columns(2)

    # Excel Export
    with col_ex:
        # Özet Veri Seti Oluştur
        summary_df = pd.DataFrame({
            "Kategori": ["Üretim", "KPI Onay", "KPI Red", "Hijyen Kusur", "Oda Sapması"],
            "Değer": [toplam_uretim, len(kpi_df)-red_s if not kpi_df.empty else 0, red_s, uyg_h, sapma_s]
        })
        _rapor_excel_export(summary_df, kpi_df, "Gunluk_Operasyonel_Ozet", bas_tarih, bas_tarih)

    # Personel Mapping (Merkezi)
    p_map = _get_personnel_display_map(engine)

    # HTML/PDF Raporu Oluştur
    summary_cards = f"""
      <div class="ozet-kart toplam">Üretim: {toplam_uretim:,}</div>
      <div class="ozet-kart red">KPI Red: {red_s}</div>
      <div class="ozet-kart red">Hijyen Kusur: {uyg_h}</div>
      <div class="ozet-kart red">Oda Sapma: {sapma_s}</div>
    """
    
    trs = ""
    # KPI Redleri ekle
    if red_s > 0:
        for _, r in kpi_df[kpi_df['karar']=='RED'].iterrows():
            p_full = p_map.get(str(r.get('kullanici', '')), r.get('kullanici', '-'))
            trs += f"<tr class='red'><td>{r.get('saat','-')}</td><td>KPI</td><td>{r.get('urun','-')}</td><td>(Uygulayıcı: {p_full}) - RED: {r.get('notlar','-')}</td></tr>"
    # Hijyen Kusurları ekle
    if uyg_h > 0:
        for _, r in hijyen_df[hijyen_df['durum']!='Sorun Yok'].iterrows():
            p_full = p_map.get(str(r.get('personel', '')), r.get('personel', '-'))
            c_full = p_map.get(str(r.get('kullanici', '')), r.get('kullanici', '-'))
            trs += f"<tr class='red'><td>{r.get('saat','-')}</td><td>Hijyen</td><td>{p_full}</td><td>(Denetleyen: {c_full}) - {r.get('durum','-')} - {r.get('aksiyon','-')}</td></tr>"
    # Oda Sapmaları ekle
    if sapma_s > 0:
        for _, r in sosts_df[sosts_df['sapma_var_mi']==1].iterrows():
            p_full = p_map.get(str(r.get('kaydeden_kullanici', '')), r.get('kaydeden_kullanici', '-'))
            trs += f"<tr class='red'><td>{r.get('olcum_zamani','-')}</td><td>S.Oda</td><td>{r.get('oda_adi','-')}</td><td>(Uygulayıcı: {p_full}) - Sapma: {r.get('sicaklik_degeri','-')}°C</td></tr>"

    if not trs:
        trs = "<tr><td colspan='4' style='text-align:center'>Bugün herhangi bir operasyonel uygunsuzluk tespit edilmemiştir.</td></tr>"

    content = f"""
    <h3>🔴 Günlük Uygunsuzluk ve Sapma Listesi</h3>
    <table>
      <thead>
        <tr><th>Saat</th><th>Kategori</th><th>Kaynak / Ürün</th><th>Açıklama / Durum</th></tr>
      </thead>
      <tbody>{trs}</tbody>
    </table>
    """
    sigs = """
        <div class="imza-kutu"><b>Vardiya Sorumlusu</b><br>Ad Soyad / İmza</div>
        <div class="imza-kutu"><b>Kalite Sorumlusu</b><br>Ad Soyad / İmza</div>
        <div class="imza-kutu"><b>Fabrika Müdürü</b><br>Ad Soyad / İmza</div>
    """
    html_rapor = _generate_base_html("GÜNLÜK OPERASYONEL DENETİM ÖZET RAPORU", "EKL-OPR-005", t_str, summary_cards, content, sigs)
    
    import json as _json
    html_json = _json.dumps(html_rapor)
    pdf_js = f"""
    <script>
    function printOperasyonel() {{
        var html = {html_json};
        var blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
        var url = URL.createObjectURL(blob);
        var win = window.open(url, '_blank');
        win.addEventListener('load', function() {{ setTimeout(function() {{ win.print(); }}, 600); }});
    }}
    </script>
    <button onclick="printOperasyonel()" style="width:100%; padding:10px 0; background:#1a2744; color:white; border:none; border-radius:5px; font-size:14px; font-weight:bold; cursor:pointer;">
        🖨️ Yönetici Özetini Yazdır (PDF)
    </button>
    """
    with col_pdf:
        st.components.v1.html(pdf_js, height=55)


# --- MODÜL 4: PERSONEL HİJYEN ÖZETİ ---
def _render_hijyen_raporu(bas_tarih, bit_tarih, matrix_filters=None):
    # Matris Filtre Hazırlığı
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
        LEFT JOIN personel p ON h.personel = p.ad_soyad 
        WHERE h.tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}' {personel_filter.replace('p.kullanici_adi', 'p.ad_soyad')}
    """
    df = run_query(sql)
    if df.empty:
        st.warning("⚠️ Bu kriterlere uygun kayıt bulunamadı."); return
    
    uygunsuzluk = df[df['durum'] != 'Sorun Yok']
    if not uygunsuzluk.empty:
        st.error(f"⚠️ {len(uygunsuzluk)} Uygunsuzluk / Devamsızlık")
        st.dataframe(uygunsuzluk, use_container_width=True, hide_index=True)
        st.bar_chart(uygunsuzluk['durum'].value_counts())
    else:
        st.success("✅ Sorunsuz")
        
    # Personel Mapping Uygula
    p_map = _get_personnel_display_map(engine)
    if 'personel' in df.columns:
        df['personel'] = df['personel'].astype(str).map(lambda x: p_map.get(x, x))
    if 'kullanici' in df.columns:
        df['kullanici'] = df['kullanici'].astype(str).map(lambda x: p_map.get(x, x))

    with st.expander("📋 Tüm Kayıtlar", expanded=True):
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    col_excel, col_pdf = st.columns(2)
    with col_excel:
        _rapor_excel_export(df, None, "Personel_Hijyen_Raporu", bas_tarih, bit_tarih)

    # HTML RAPORU OLUŞTUR
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
        if dur == 'Sorun Yok': badge = f'<span class="badge bg-green">Sorun Yok</span>'
        else: badge = f'<span class="badge {"bg-red" if "Ateş" in dur else "bg-orange"}">{dur}</span>'
            
        bg_class = ' class="highlight-yellow"' if dur != 'Sorun Yok' else ''
        
        aksiyon = str(r.get('aksiyon','-'))
        if aksiyon != '-': aksiyon = f"<b>DÖF:</b> {aksiyon}"
        
        c_full = r.get('kullanici', 'Kontrolör')
        trs += f"<tr{bg_class}><td>{r.get('saat','')}</td><td>{r.get('bolum','')}</td><td>{r.get('personel','')}</td><td>{r.get('vardiya','')}</td><td>{badge}</td><td>{aksiyon}</td><td>{c_full}</td></tr>"
        
    content = f"""
    <table>
      <thead>
        <tr><th>Saat</th><th>Bölüm</th><th>Personel Adı</th><th>Vardiya</th><th>Durum (Kök Neden)</th><th>DÖF / Alınan Aksiyon</th><th>Kontrolör</th></tr>
      </thead>
      <tbody>{trs}</tbody>
    </table>
    """
    sigs = """
        <div class="imza-kutu"><b>Kontrolü Yapan Personel</b><br>Ad Soyad / İmza</div>
        <div class="imza-kutu"><b>Vardiya Amiri</b><br>Ad Soyad / İmza</div>
        <div class="imza-kutu"><b>Kalite Yönetimi</b><br>Ad Soyad / İmza</div>
    """
    html_rapor = _generate_base_html("PERSONEL HİJYEN VE SAĞLIK KONTROL RAPORU", "EKL-KYS-HIJ-002", f"{bas_tarih} / {bit_tarih}", cards, content, sigs)
    
    import json as _json
    html_json = _json.dumps(html_rapor)
    pdf_js = f"""
    <script>
    function printHijyenReport() {{
        var html = {html_json};
        var blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
        var url = URL.createObjectURL(blob);
        var win = window.open(url, '_blank');
        win.addEventListener('load', function() {{ setTimeout(function() {{ win.print(); }}, 600); }});
    }}
    </script>
    <button onclick="printHijyenReport()" style="width:100%; padding:10px 0; background:#8B0000; color:white; border:none; border-radius:5px; font-size:14px; font-weight:bold; cursor:pointer; margin-top:20px;">
        🖨️ Yazdır / PDF Kaydet (Hijyen)
    </button>
    """
    st.components.v1.html(pdf_js, height=75)


# --- MODÜL 5: TEMİZLİK TAKİP RAPORU ---
def _render_temizlik_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT id, tarih, saat, bolum, alan_ekipman, kimyasal, durum, atp_swab, kullanici FROM temizlik_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if not df.empty:
        # Personel Mapping Uygula
        p_map = _get_personnel_display_map(engine)
        if 'kullanici' in df.columns:
            df['kullanici'] = df['kullanici'].astype(str).map(lambda x: p_map.get(x, x))

        st.success(f"✅ {len(df)} görev tamamlandı.")
        st.bar_chart(df.groupby('bolum').size())
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        c_ex, c_pd = st.columns(2)
        with c_ex:
            _rapor_excel_export(df, None, "Temizlik_Takip_Raporu", bas_tarih, bit_tarih)
    else:
        st.warning("Kayıt yok")
        return

    # HTML RAPORU OLUŞTUR
    toplam = len(df)
    onaylanan = len(df[df['durum'] == 'GÖRSEL ONAY'])
    reddedilen = toplam - onaylanan
    
    cards = f"""
      <div class="ozet-kart toplam">Planlanan Temizlik: {toplam} Alan</div>
      <div class="ozet-kart onay">Doğrulanan (ATP Dahil): {onaylanan}</div>
      <div class="ozet-kart red">Eksik / Uygunsuz: {reddedilen}</div>
    """
    
    trs = ""
    for _, r in df.iterrows():
        dur = str(r.get('durum',''))
        badge = f'<span class="badge {"bg-green" if "ONAY" in dur else "bg-red"}">{dur}</span>'
        bg_class = ' class="highlight-yellow"' if 'RED' in dur else ''
        
        atp = str(r.get('atp_swab','Gerekli Değil'))
        u_full = r.get('kullanici', 'Personel')
        trs += f"<tr{bg_class}><td>{r.get('saat','')}</td><td>{r.get('bolum','')}</td><td>{r.get('alan_ekipman','')}</td><td>{r.get('kimyasal','')}</td><td>{badge}</td><td>{atp}</td><td>{u_full}</td></tr>"
        
    content = f"""
    <table>
      <thead>
        <tr><th>Saat</th><th>Bölüm</th><th>Alan / Ekipman</th><th>Kimyasal / Dozaj</th><th>Doğrulama Durumu (Kritik)</th><th>ATP Swab (RLU)</th><th>Gerçekleştiren</th></tr>
      </thead>
      <tbody>{trs}</tbody>
    </table>
    """
    sigs = """
        <div class="imza-kutu"><b>Temizliği Yapan Personel</b><br>Ad Soyad / İmza</div>
        <div class="imza-kutu"><b>Vardiya Şefi</b><br>Ad Soyad / İmza</div>
        <div class="imza-kutu"><b>Kalite Doğrulama Uzmanı</b><br>Ad Soyad / İmza</div>
    """
    html_rapor = _generate_base_html("ALAN VE EKİPMAN TEMİZLİK DOĞRULAMA RAPORU", "EKL-KYS-TEM-003", f"{bas_tarih} / {bit_tarih}", cards, content, sigs)
    
    import json as _json
    html_json = _json.dumps(html_rapor)
    pdf_js = f"""
    <script>
    function printTemizlikReport() {{
        var html = {html_json};
        var blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
        var url = URL.createObjectURL(blob);
        var win = window.open(url, '_blank');
        win.addEventListener('load', function() {{ setTimeout(function() {{ win.print(); }}, 600); }});
    }}
    </script>
    <button onclick="printTemizlikReport()" style="width:100%; padding:10px 0; background:#8B0000; color:white; border:none; border-radius:5px; font-size:14px; font-weight:bold; cursor:pointer; margin-top:20px;">
        🖨️ Yazdır / PDF Kaydet (Temizlik)
    </button>
    """
    st.components.v1.html(pdf_js, height=75)


# --- MODÜL 6: LOKASYON & PROSES HARİTASI ---
def _render_interactive_location(loc_id, loc_df, tree, proses_map, level=0):
    try: loc_row = loc_df[loc_df['id'] == loc_id].iloc[0]
    except: return
    l_ad, l_tip = loc_row['ad'], loc_row['tip']
    icon = {"Kat": "🏗️", "Bölüm": "🏢", "Hat": "⚙️", "Ekipman": "🔧"}.get(l_tip, "📍")
    p_badges = ""
    if not proses_map.empty:
        p_list = proses_map[proses_map['lokasyon_id'] == loc_id]
        for _, p in p_list.iterrows():
            if pd.notna(p['proses_adi']): p_badges += f" <span style='background:#E8F8F5; color:#117864; padding:2px 6px; border-radius:4px; font-size:0.8em;'>{p.get('ikon','🔹')} {p['proses_adi']}</span>"
    children = tree.get(loc_id, [])
    if children:
        with st.expander(f"{icon} {l_ad} ({len(children)}) {l_tip}", expanded=(l_tip == 'Kat')):
            if p_badges: st.markdown(p_badges, unsafe_allow_html=True)
            for cid in children: _render_interactive_location(cid, loc_df, tree, proses_map, level + 1)
    else:
        st.markdown(f'<div style="margin-left:20px; border-left:4px solid #FF4B4B; padding:5px;">{icon} <b>{l_ad}</b> {p_badges}</div>', unsafe_allow_html=True)

def _render_graphviz_map(loc_df, tree, roots, proses_map):
    dot = 'digraph FactoryMap { rankdir=LR; node [shape=box, style=filled, fontname=Arial, fontsize=10];\n'
    def add_dot_recursive(loc_id):
        try: row = loc_df[loc_df['id'] == loc_id].iloc[0]
        except: return ""
        ad, tip = row['ad'], row['tip']
        children = tree.get(loc_id, [])
        out = ""
        if children:
            out += f'subgraph cluster_{loc_id} {{ label="{ad}"; style=filled; fillcolor=ivory; '
            for cid in children: out += add_dot_recursive(cid)
            out += '} '
        else:
            out += f'node_{loc_id} [label="{ad}\\n({tip})", fillcolor=lightgrey]; '
        return out
    for rid in roots: dot += add_dot_recursive(rid)
    dot += '}'
    st.graphviz_chart(dot, use_container_width=True)

def _render_lokasyon_haritasi():
    st.info("Kurumsal Lokasyon Haritası")
    loc_df = run_query("SELECT * FROM lokasyonlar WHERE aktif = 1")
    try:
        proses_map = run_query("SELECT lpa.lokasyon_id, pt.ad as proses_adi, pt.ikon FROM lokasyon_proses_atama lpa JOIN proses_tipleri pt ON lpa.proses_tip_id = pt.id WHERE lpa.aktif = 1")
    except:
        proses_map = pd.DataFrame()
    if loc_df.empty: st.warning("Veri yok"); return
    tree, roots = {}, []
    ids = set(loc_df['id'].unique())
    for _, r in loc_df.iterrows():
        lid, pid = int(r['id']), r['parent_id']
        if pd.isna(pid) or pid == 0 or int(pid) not in ids: roots.append(lid)
        else: tree.setdefault(int(pid), []).append(lid)
    tip = st.radio("Görünüm:", ["İnteraktif", "Şematik"], horizontal=True)
    if tip == "İnteraktif":
        for rid in roots: _render_interactive_location(rid, loc_df, tree, proses_map)
    else:
        _render_graphviz_map(loc_df, tree, roots, proses_map)
    
    st.divider()
    if st.button("🖨️ Görünümü PDF Olarak Yazdır"):
        st.info("İpucu: Açılan pencerede 'PDF olarak kaydet' seçeneğini kullanabilirsiniz.")
        st.components.v1.html("<script>setTimeout(function(){ window.print(); }, 500);</script>", height=0)


# --- MODÜL 7: PERSONEL ORGANİZASYON ŞEMASI ---
def _render_dept_recursive(dept_id, dept_name, all_depts, pers_df, is_expanded=True):
    sub = all_depts[all_depts['ana_departman_id'] == dept_id]
    staff = pers_df[pers_df['departman_id'] == dept_id].sort_values('pozisyon_seviye')
    all_sub_ids = get_all_sub_department_ids(dept_id)
    tree_total = len(pers_df[pers_df['departman_id'].isin(all_sub_ids)])

    with st.expander(f"🏢 {dept_name} | Toplam: {tree_total}", expanded=is_expanded):
        if not staff.empty:
            for _, p in staff.iterrows():
                st.markdown(f"• {get_position_icon(p['pozisyon_seviye'])} **{p['ad_soyad']}** ({p['gorev'] or p['rol']})")
        for _, s in sub.iterrows():
            _render_dept_recursive(s['id'], s['bolum_adi'], all_depts, pers_df, False)

def _bolum_toplam_personel(dept_id, all_depts, pers_df):
    """Bölüm + tüm alt bölümlerin toplam personel sayısını döner."""
    from logic.data_fetcher import get_all_sub_department_ids
    alt_ids = get_all_sub_department_ids(dept_id)
    return int(pers_df[pers_df['departman_id'].isin(alt_ids)].shape[0])

def _render_kurumsal_kimlik(all_depts, pers_df):
    """Raporun üstünde ana bölümlerin çalışan sayı kartlarını gösterir."""
    st.subheader("🏛️ Kurumsal Kimlik — Bölüm Bazlı Çalışan Dağılımı")
    toplam = len(pers_df)
    st.caption(f"Toplam Aktif Personel: **{toplam}**")

    ana_bolumler = all_depts[all_depts['ana_departman_id'].isna() |
                             (all_depts['ana_departman_id'] == 1)]
    ana_bolumler = ana_bolumler[ana_bolumler['id'] != 1]

    satirlar = [ana_bolumler.iloc[i:i+4] for i in range(0, len(ana_bolumler), 4)]
    for satir in satirlar:
        kolonlar = st.columns(len(satir))
        for col, (_, bolum) in zip(kolonlar, satir.iterrows()):
            sayi = _bolum_toplam_personel(bolum['id'], all_depts, pers_df)
            oran = f"%{round(sayi / toplam * 100, 1)}" if toplam > 0 else "%0"
            col.metric(label=bolum['bolum_adi'], value=sayi, delta=oran)

def _render_organizasyon_semasi():
    """Modül 7: Personel Organizasyon Şeması (ADIM 3 - Kurumsal PDF)."""
    pers_df = get_personnel_hierarchy()
    if pers_df.empty: 
        st.warning("Hiyerarşi oluşturmak için personel verisi bulunamadı.")
        return
        
    all_depts = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif = 1")

    # 0. Kurumsal Kimlik — Bölüm Çalışan Sayıları
    _render_kurumsal_kimlik(all_depts, pers_df)
    st.divider()

    # 1. Ekran Görünümü (Expander Tree)
    st.subheader("🏢 Mevcut Hiyerarşik Yapı")
    top = all_depts[all_depts['ana_departman_id'].isna() | (all_depts['ana_departman_id'] == 1)]
    for _, d in top.iterrows():
        if d['id'] != 1: 
            _render_dept_recursive(d['id'], d['bolum_adi'], all_depts, pers_df, True)
    
    st.divider()
    
    # 2. Kurumsal PDF İndirme (ADIM 3 - ReportLab Integration)
    from modules.qdms.pdf_uretici import org_chart_pdf_uret
    try:
        pdf_bytes = org_chart_pdf_uret(engine, all_depts, pers_df)
        if pdf_bytes:
            st.download_button(
                label="📥 Kurumsal Organizasyon Şemasını İndir (PDF)",
                data=pdf_bytes,
                file_name=f"EKL-KYS-ORG-001_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="BRCGS/IFS standartlarında, Format Kanunu'na uygun landscape PDF dökümanı üretir."
            )
    except Exception as e:
        st.error(f"Organizasyon şeması PDF'i üretilirken bir hata oluştu: {e}")
# --- YENİ: SOĞUK ODA TEKLİ RAPOR JENERATÖRÜ (V3.1 - Madde 13 Uyumlu) ---

def _get_html_styles():
    """Rapor için CSS stillerini döndürür (Madde 13 - Tek Sorumluluk)."""
    return """
    <style>
      @page { size: A4; margin: 10mm 15mm 10mm 15mm; }
      @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
      body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 10px; color: #333; background: white; margin: 0; padding: 0; }
      .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #8B0000; padding-bottom: 8px; margin-bottom: 15px; }
      .header-logo img { height: 45px; }
      .header-title { text-align: center; flex-grow: 1; margin: 0 20px; }
      .header-title h1 { font-size: 18px; color: #1a2744; margin: 0 0 2px 0; text-transform: uppercase; letter-spacing: 1px; }
      .header-title h2 { font-size: 14px; color: #8B0000; margin: 0; font-weight: bold; }
      .header-meta { text-align: right; font-size: 9px; color: #555; white-space: nowrap; }
      .info-bar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; background: #f4f7f9; border: 1px solid #d1d9e6; border-radius: 6px; padding: 10px; margin-bottom: 20px; }
      .info-item { display: flex; flex-direction: column; align-items: center; border-right: 1px solid #d1d9e6; }
      .info-item:last-child { border-right: none; }
      .info-label { font-size: 8px; color: #7f8c8d; text-transform: uppercase; font-weight: 700; margin-bottom: 3px; }
      .info-value { font-size: 12px; color: #2c3e50; font-weight: 700; }
      table { width: 100%; border-collapse: collapse; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
      th { background-color: #1a2744; color: white; padding: 8px 4px; text-align: center; border: 1px solid #2c3e50; font-size: 10px; text-transform: uppercase; }
      td { padding: 8px 4px; border: 1px solid #e0e0e0; text-align: center; vertical-align: middle; font-size: 11px; }
      tr:nth-child(even) { background-color: #fcfdfe; }
      .takip-row { background-color: #f0fdf4 !important; }
      .badge { padding: 3px 8px; border-radius: 12px; font-size: 9px; font-weight: bold; text-transform: uppercase; }
      .bg-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
      .bg-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
      .bg-gray { background: #f3f4f6; color: #4b5563; border: 1px solid #e5e7eb; }
      .deviation-box { margin-top: 20px; border: 1px solid #fecaca; background: #fffafb; padding: 15px; border-radius: 8px; }
      .deviation-title { color: #b91c1c; font-size: 13px; font-weight: 800; margin-bottom: 10px; display: flex; align-items: center; }
      .deviation-list { margin: 0; padding-left: 15px; list-style-type: none; }
      .deviation-list li { margin-bottom: 12px; border-left: 3px solid #ef4444; padding-left: 10px; }
      .val { font-weight: bold; color: #b91c1c; }
      .follow-up-text { display: block; margin-top: 5px; font-style: italic; color: #15803d; font-weight: 600; font-size: 10px; }
      .imza-alani { margin-top: 50px; }
      .imza-tablo { display: flex; gap: 20px; }
      .imza-kutu { flex: 1; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px 10px 50px 10px; text-align: center; background: #fdfdfd; }
      .imza-kutu b { display: block; color: #1e293b; margin-bottom: 10px; border-bottom: 2px solid #f1f5f9; padding-bottom: 5px; font-size: 11px; }
      .footer { margin-top: 30px; border-top: 2px solid #f1f5f9; padding-top: 10px; display: flex; justify-content: space-between; font-size: 8px; color: #94a3b8; font-weight: 600; }
    </style>
    """

def _match_deviations_and_followups(room_df):
    """Sapma ve DÖF (takip) kayıtlarını sıralı indeks bazlı eşleştirir (Backend Mantığı)."""
    room_df = room_df.sort_values(by='zaman').copy()
    room_df['is_takip_eff'] = False
    room_df['linked_followup_idx'] = None
    
    last_deviation_idx = None
    for idx, row in room_df.iterrows():
        is_sapma = row.get('sapma_var_mi', 0) == 1
        is_plansiz = pd.isna(row.get('plan_id')) and pd.notnull(row.get('sicaklik_degeri'))
        is_manuel_takip = row.get('is_takip', 0) == 1 or row.get('plan_is_takip', 0) == 1
        
        if is_sapma:
            last_deviation_idx = idx
        elif (is_plansiz or is_manuel_takip) and last_deviation_idx is not None:
            # Sapmadan sonraki ilk plansız veya manuel takip ölçümü DÖF'tür
            room_df.at[idx, 'is_takip_eff'] = True
            room_df.at[last_deviation_idx, 'linked_followup_idx'] = idx
            last_deviation_idx = None # Eşleşme tamamlandı
            
    return room_df

def _format_deviation_list_item(row, room_df, p_map, min_s, max_s):
    """Tek bir sapma satırı ve varsa bağlı DÖF'ü için HTML üretir."""
    st_zaman = pd.to_datetime(row['zaman']).strftime('%H:%M') if pd.notnull(row['zaman']) else "-"
    k_saat = pd.to_datetime(row['kesin_saat']).strftime('%H:%M') if 'kesin_saat' in row and pd.notnull(row['kesin_saat']) else st_zaman
    d_err = f"{row['sicaklik_degeri']} °C"
    kisi_err = p_map.get(str(row['kaydeden_kullanici']), str(row['kaydeden_kullanici']))
    
    hedef = "olması gereken limitlerin dışına çıkarak"
    try:
        val = float(row['sicaklik_degeri'])
        if val > max_s: hedef = f"maksimum <span class='val'>{max_s} °C</span> limitini aşarak"
        elif val < min_s: hedef = f"minimum <span class='val'>{min_s} °C</span> limitinin altına düşerek"
    except: pass
        
    aciklama = str(row.get('sapma_aciklamasi', ''))
    beyan_html = f"<div class='follow-up-text' style='color:#666; border-left-color:#ffcc80;'><i>Nedeni:</i> {aciklama}</div>" if aciklama not in ('None', 'nan', '') else ""
    
    html = f"<li><b>{st_zaman}</b> periyodu ölçümünde (Kayıt Saati: <span class='val'>{k_saat}</span>), {hedef} <span class='val'>{d_err}</span> sıcaklık ölçümü kaydedilmiştir. (Yetkili: {kisi_err}){beyan_html}"
    
    # Bağlı Takip (DÖF) varsa ekle
    f_idx = row.get('linked_followup_idx')
    if f_idx is not None and f_idx in room_df.index:
        follow = room_df.loc[f_idx]
        t_saat = pd.to_datetime(follow['kesin_saat']).strftime('%H:%M') if pd.notnull(follow['kesin_saat']) else "?"
        t_val = f"{follow['sicaklik_degeri']} °C"
        try:
            sapma_dt = pd.to_datetime(row['kesin_saat']) if pd.notnull(row['kesin_saat']) else pd.to_datetime(row['zaman'])
            follow_dt = pd.to_datetime(follow['kesin_saat']) if pd.notnull(follow['kesin_saat']) else pd.to_datetime(follow['zaman'])
            fark = int((follow_dt - sapma_dt).total_seconds() / 60)
            fark = max(0, fark) # Negatif süre koruması
        except: fark = "?"
        html += f"<span class='follow-up-text'>↳ Düzeltici Faaliyet: Sapmadan {fark} dk sonra ({t_saat}) yapılan <b>takip ölçümünde</b> sıcaklığın {t_val}'ye dönerek limitler dahiline girdiği teyit edilmiştir.</span>"
    
    return html + "</li>"

def _generate_single_room_html(oda, room_df, bas_tarih, bit_tarih, p_map):
    """Soğuk oda raporu ana fonksiyonu (Madde 11 - Frontend/Backend Ayrımı)."""
    room_df = _match_deviations_and_followups(room_df)
    
    rapor_tarihi = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%d.%m.%Y %H:%M')
    min_s = float(room_df['min_sicaklik'].iloc[0]) if not room_df.empty and 'min_sicaklik' in room_df.columns and pd.notnull(room_df['min_sicaklik'].iloc[0]) else 0
    max_s = float(room_df['max_sicaklik'].iloc[0]) if not room_df.empty and 'max_sicaklik' in room_df.columns and pd.notnull(room_df['max_sicaklik'].iloc[0]) else 0
    sorumlu = room_df['sorumlu_personel'].iloc[0] if not room_df.empty and 'sorumlu_personel' in room_df.columns else "Atanmadı"
    
    sapma_count = len(room_df[room_df['sapma_var_mi'] == 1])
    takip_count = len(room_df[room_df['is_takip_eff'] == True])
    
    durum_html = f'<span class="info-value" style="color:#2e7d32;">✅ Uygun</span>'
    if sapma_count > 0:
        msg = f"({takip_count} Takip ile kapatıldı)" if takip_count > 0 else "(Müdahale Bekleniyor)"
        durum_html = f'<span class="info-value" style="color:#c62828;">⚠️ {sapma_count} Sapma {msg}</span>'

    html = f"<html><head>{_get_html_styles()}</head><body>"
    html += f"""
    <div class="header">
        <div class="header-logo"><img src="https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png"></div>
        <div class="header-title"><h1>SOĞUK ODA İZLEME FORMU</h1><h2>{oda} Sicil Kartı</h2></div>
        <div class="header-meta">Kod: EKL-SO-004<br>Rev: 04<br>Baskı: {rapor_tarihi}</div>
    </div>
    <div class="info-bar">
        <div class="info-item"><span class="info-label">İzleme Tarihi</span><span class="info-value">{bas_tarih} / {bit_tarih}</span></div>
        <div class="info-item"><span class="info-label">Limitler</span><span class="info-value">{min_s}°C / {max_s}°C</span></div>
        <div class="info-item"><span class="info-label">Sorumlu</span><span class="info-value">{sorumlu}</span></div>
        <div class="info-item"><span class="info-label">Durum</span>{durum_html}</div>
    </div>
    <table><thead><tr><th>Aralık</th><th>Saat</th><th>Değer</th><th>Durum</th><th>Personel</th><th>Mühür</th></tr></thead><tbody>
    """
    
    for idx, row in room_df.iterrows():
        is_takip = row['is_takip_eff']
        is_sapma = row.get('sapma_var_mi', 0) == 1
        k_saat = pd.to_datetime(row['kesin_saat']).strftime('%H:%M') if pd.notnull(row['kesin_saat']) else "-"
        val = f"{row['sicaklik_degeri']} °C" if pd.notnull(row['sicaklik_degeri']) else "-"
        
        badge = '<span class="badge bg-green">Uygun</span>'
        if is_takip: badge = '<span class="badge bg-green" style="background-color:#c8e6c9;">Düzeltildi</span>'
        elif is_sapma: badge = '<span class="badge bg-red">Sapma</span>'
        elif pd.isna(row['sicaklik_degeri']): badge = '<span class="badge bg-gray">KAYIT EDİLMEDİ</span>'
        
        kisi = p_map.get(str(row['kaydeden_kullanici']), "-")
        log = pd.to_datetime(row['kayit_zamani']).strftime('%H:%M') if pd.notnull(row['kayit_zamani']) else "-"
        
        tr_style = ' class="takip-row"' if is_takip else ''
        # ANAYASA v4: PDF Aralığı '00:00 - 04:00' formatında gösterilir.
        t_start = pd.to_datetime(row['zaman']).strftime('%H:%M') if pd.notnull(row['zaman']) else "??"
        t_end = pd.to_datetime(row.get('bitis_zamani')).strftime('%H:%M') if pd.notnull(row.get('bitis_zamani')) else "??"
        
        aralik = '<i>Takip (DÖF)</i>' if is_takip else f"{t_start} - {t_end}"
        
        html += f"<tr{tr_style}><td>{aralik}</td><td><b>{k_saat}</b></td><td>{val}</td><td>{badge}</td><td>{kisi}</td><td>{log}</td></tr>"

    html += "</tbody></table>"
    
    if sapma_count > 0:
        sapmalar = room_df[room_df['sapma_var_mi'] == 1]
        items = "".join([_format_deviation_list_item(s, room_df, p_map, min_s, max_s) for _, s in sapmalar.iterrows()])
        html += f'<div class="deviation-box"><div class="deviation-title">🚨 Kritik Sapma ve DÖF Raporu</div><ul class="deviation-list">{items}</ul></div>'

    html += """<div class="imza-alani"><div class="imza-tablo">
        <div class="imza-kutu"><b>Personel</b>İmza</div><div class="imza-kutu"><b>Sorumlu</b>İmza</div><div class="imza-kutu"><b>Kalite</b>İmza</div>
    </div></div><div class="footer"><span>QMS v3.1</span><span>Gizlilik: Dahili</span></div></body></html>"""
    
    return html


# --- MODÜL 8: SOĞUK ODA İZLEME ---
def _render_soguk_oda_izleme(bas_tarih, bit_tarih):
    """📊 Seçili tarih aralığındaki ölçüm matrisi görünümü. (00:00 - 00:00 Uyumlu)"""
    st.subheader("❄️ Günlük Sıcaklık İzleme")
    if not engine:
        st.error("Veritabanı bağlantısı yok.")
        return

    # --- YENİ: Raporu Revize Et (Sıklık Senkronizasyonu) ---
    st.info("💡 İpucu: Ölçüm sıklığını (Sabah/Akşam/Gece) değiştirdiyseniz, rapor slotlarını güncellemek için aşağıdaki butonu kullanın.")
    if st.button("🔄 Ölçüm Sıklığına Göre Raporu Revize Et", use_container_width=True):
        from soguk_oda_utils import plan_uret
        # Bugün ve Yarın için planları tazele (Canlı DB Uyumlu)
        plan_uret(engine, gun_sayisi=2)
        st.success("✅ Rapor slotları sistemdeki güncel ölçüm sıklığına göre yeniden planlandı.")
        st.rerun()

    df_matris = get_matrix_data(engine, bas_tarih, bit_tarih)
    if not df_matris.empty:
        # Zaman değerini "04.03 08:00 - 09:00" formatına dönüştür (Dinamik Aralık)
        def format_aralikli_saat(row):
            """ANAYASA v4: Saatleri '00:00 - 04:00' formatında döndürür."""
            try:
                # pandas datetime veya str gelebilir, standardize et
                def _to_hm(val):
                    if pd.isnull(val): return "??"
                    dt = pd.to_datetime(val)
                    return dt.strftime('%H:%M')

                t_start = _to_hm(row['zaman'])
                t_end = _to_hm(row.get('bitis_zamani'))
                
                if t_end == "??":
                    # Fallback
                    dt_obj = pd.to_datetime(row['zaman'])
                    t_end = (dt_obj + pd.Timedelta(hours=1)).strftime('%H:%M')
                    
                return f"{t_start} - {t_end}"
            except:
                return str(row.get('zaman'))

        df_matris['zaman_str'] = df_matris.apply(format_aralikli_saat, axis=1)
        
        status_icons = {'BEKLIYOR': '⏳', 'TAMAMLANDI': '✅', 'GECIKTI': '⚠️', 'ATILDI': '❌', 'MANUEL': '📝'}
        
        def get_display_icon(row):
            is_null = pd.isna(row.get('sicaklik_degeri'))
            is_takip_eff = (row.get('is_takip', 0) == 1) or (row.get('plan_is_takip', 0) == 1)
            
            if not is_null and row.get('sapma_var_mi') == 1:
                return '🚨'
            
            # Takip (DÖF) Görevi İkonu
            if is_takip_eff:
                if not is_null: return '🩺✅' # Tamamlanan takip
                return '🩺' # Bekleyen takip
            
            # Eğer ölçüm yoksa ve durum GECIKTI ise özel etiketle
            if is_null and row.get('durum') == 'GECIKTI':
                return '⚠️ KAYIT EDİLMEDİ'
                
            return status_icons.get(row.get('durum'), '📝')
            
        def format_display(row):
            icon = get_display_icon(row)
            val = str(row.get('sicaklik_degeri')).replace('nan', '')
            if 'KAYIT EDİLMEDİ' in icon:
                return icon
            return f"{icon} {val}".strip()
            
        df_matris['display'] = df_matris.apply(format_display, axis=1)
        
        # Sorumlu davranması için sıralama: Ölçüm yapılanları (sicaklik_degeri nan olmayanları) öne al
        # Böylece aynı slota düşen GECIKTI veya MANUEL kayıtlardan, içi dolu olan (MANUEL) pivotta gösterilir.
        df_matris['has_value'] = df_matris['sicaklik_degeri'].notna()
        df_matris = df_matris.sort_values(by=['oda_adi', 'zaman_str', 'has_value'], ascending=[True, True, False])

        # 🧪 Önemli: Pivot yerine görseldeki tam detaylı tablo yapısını (Aralik, Saat, Değer, Durum, Personel, Mühür) kurguluyoruz.
        p_map = _get_personnel_display_map(engine)
        
        def format_row_data(row):
            # 1. Aralık
            aralik = format_aralikli_saat(row).split(' ')[-1] # Sadece saati al (07:00 vb)
            # 2. Saat
            saat = pd.to_datetime(row['kesin_saat']).strftime('%H:%M') if pd.notnull(row['kesin_saat']) else "-"
            # 3. Değer
            deger = f"{row['sicaklik_degeri']} °C" if pd.notnull(row['sicaklik_degeri']) else "-"
            # 4. Durum
            is_sapma = row.get('sapma_var_mi') == 1
            durum = "🚨 Sapma" if is_sapma else ("Uygun" if pd.notnull(row['sicaklik_degeri']) else "Bekleniyor")
            # 5. Personel
            personel = p_map.get(str(row['kaydeden_kullanici']), str(row['kaydeden_kullanici'])) if pd.notnull(row['kaydeden_kullanici']) else "-"
            # 6. Mühür
            muhur = saat # Görselde Mühür = Saat (Kayıt Saati) olarak görünüyor
            
            return pd.Series([aralik, saat, deger, durum, personel, muhur])

        # Sadece ölçüm olanları detaylı tabloda gösterelim (Görseldeki gibi)
        df_display = df_matris[df_matris['sicaklik_degeri'].notna()].copy()
        if not df_display.empty:
            df_table = df_display.apply(format_row_data, axis=1)
            df_table.columns = ['Aralık', 'Saat', 'Değer', 'Durum', 'Personel', 'Mühür']
            st.dataframe(df_table.sort_values(by=['Aralık', 'Saat']), use_container_width=True, hide_index=True)
        else:
            st.info("Henüz kaydedilmiş bir ölçüm bulunmuyor. Planlanan slotlar sistemde takiptedir.")

        # Matrix Pivot (Pivot görünümünde gecikmeleri daha net gösterelim)
        with st.expander("📊 Tüm Odalar Özet Matrisi (Pivot Görünümü)"):
            pivot = df_matris.pivot_table(index='oda_adi', columns='zaman_str', values='display', 
                                        aggfunc=lambda x: ", ".join([v for v in x.astype(str).unique() if v.strip() and v != 'nan'])).fillna('⏳ BEKLENİYOR')
            st.dataframe(pivot, use_container_width=True)
        
        # Saha Uygulayıcıları Detay Tablosu (Zaten yukarıdaki yeni tablo bu işi görüyor, eskiyi silebiliriz)
        
        # Excel & Odalara Özel PDF Butonları
        st.divider()
        st.subheader("🖨️ A4 Detaylı Oda Raporları (PDF)")
        st.caption("Her bir soğuk oda için BRCGS standartlarında ayrı ayrı hazırlanmış detaylı ve sapma açıklamalı PDF raporlarını aşağıdan yazdırabilirsiniz.")
        
        c_ex, _ = st.columns(2)
        with c_ex:
            _rapor_excel_export(pivot.reset_index(), None, "Soguk_Oda_Izleme_Matrisi", bas_tarih, bit_tarih)
        
        # Her oda için ayrı PDF butonu (Grid düzeni)
        unique_rooms = df_matris['oda_adi'].unique()
        room_cols = st.columns(3)
        
        import json as _json
        p_map = _get_personnel_display_map(engine) if engine else {}
        
        for idx, oda in enumerate(unique_rooms):
            room_df = df_matris[df_matris['oda_adi'] == oda].copy()
            room_df = room_df.sort_values(by='zaman')
            
            html_rapor = _generate_single_room_html(oda, room_df, bas_tarih, bit_tarih, p_map)
            html_json = _json.dumps(html_rapor)
            
            # Benzersiz JS ID
            safe_oda_id = f"btn_{idx}_{int(time.time())}"
            pdf_js = f"""
            <script>
            function printRoom_{safe_oda_id}() {{
                var html = {html_json};
                var win = window.open('', '_blank');
                win.document.open();
                win.document.write(html);
                win.document.close();
                setTimeout(function() {{ win.print(); }}, 600);
            }}
            </script>
            <button onclick="printRoom_{safe_oda_id}()" style="width:100%; padding:10px 0; background:#1a2744; color:white; border:none; border-radius:5px; font-size:13px; font-weight:bold; cursor:pointer;">
                📄 {oda} Özeti
            </button>
            """
            
            with room_cols[idx % 3]:
                st.components.v1.html(pdf_js, height=55)
    else:
        st.info("Bu tarih için henüz planlanmış ölçüm bulunmuyor.")


# --- MODÜL 9: SOĞUK ODA TREND ---
def _render_soguk_oda_trend():
    """📈 Sıcaklık trend analizi."""
    st.subheader("📈 Sıcaklık Trend Analizi")
    if not engine: return
    rooms = run_query("SELECT id, oda_adi FROM soguk_odalar WHERE aktif = 1")
    if rooms.empty:
        st.info("Kayıtlı oda bulunamadı.")
        return
    target = st.selectbox("Oda Seçiniz:", rooms['id'], format_func=lambda x: rooms[rooms['id']==x]['oda_adi'].iloc[0])
    df = get_trend_data(engine, target)
    if not df.empty:
        fig = px.line(df, x='olcum_zamani', y='sicaklik_degeri', title="Sıcaklık Değişim Trendi")
        fig.add_hline(y=float(df['min_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        fig.add_hline(y=float(df['max_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
        
        # Trend PDF Desteği
        if st.button("🖨️ Trend Raporu PDF Hazırla (Görünüm Yazdır)"):
            st.info("İpucu: Sayfa açıldığında tarayıcı 'Yazdır' (Ctrl+P) özelliği ile grafiği PDF olarak kaydedebilirsiniz.")
            time.sleep(0.3)
            st.components.v1.html("<script>window.print();</script>", height=0)
    else:
        st.info("Kayıtlı veri bulunamadı.")


# --- MODÜL 5.1: MAP ÜRETİM RAPORLARI (KURUMSAL ENTEGRASYON) ---
def _render_map_raporlari(bas_tarih, bit_tarih):
    """📦 Kurumsal Raporlama altında MAP vardiyalarını listeler ve PDF sunar."""
    st.subheader("📦 MAP Makinası Üretim Raporları")
    st.caption(f"🗓️ {bas_tarih} - {bit_tarih} arası tüm kapalı vardiyalar")
    
    from ui.map_uretim import map_db as mdb
    from ui.map_uretim import map_rapor_pdf as mpdf
    import json as _json

    # 1. Veri Çekme
    sql = """SELECT v.id, v.tarih, v.makina_no, v.vardiya_no, 
                    COALESCE(p.ad_soyad, v.operator_adi) as operator_adi, 
                    v.gerceklesen_uretim, v.durum 
             FROM map_vardiya v
             LEFT JOIN personel p ON v.operator_adi = p.kullanici_adi
             WHERE v.tarih BETWEEN :bas AND :bit AND v.durum='KAPALI'
             ORDER BY v.tarih DESC, v.id DESC"""
    
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params={"bas": str(bas_tarih), "bit": str(bit_tarih)})

    if df.empty:
        st.info("Seçilen tarih aralığında kapalı MAP vardiyası bulunamadı.")
        return

    # 2. Tablo Gösterimi
    df_display = df.copy()
    df_display.columns = ["ID", "Tarih", "Makina", "Vardiya", "Operatör", "Üretim (pk)", "Durum"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.divider()
    st.write("### 🖨️ Rapor Seçimi ve PDF Yazdırma")
    
    # Grid yapısında butonlar
    cols = st.columns(3)
    for idx, row in df.iterrows():
        label = f"📄 {row['tarih']} - {row['makina_no']} (V{row['vardiya_no']})"
        
        # HTML Rapor Hazırla
        html_rapor = mpdf.uret_is_raporu_html(engine, int(row['id']))
        if html_rapor:
            html_json = _json.dumps(html_rapor)
            safe_id = f"map_pdf_{row['id']}_{int(time.time())}"
            pdf_js = f"""
            <script>
            function printMap_{safe_id}() {{
                var html = {html_json};
                var win = window.open('', '_blank');
                win.document.open();
                win.document.write(html);
                win.document.close();
                setTimeout(function() {{ win.print(); }}, 600);
            }}
            </script>
            <button onclick="printMap_{safe_id}()" style="width:100%; padding:10px 0; background:#8B0000; color:white; border:none; border-radius:5px; font-size:12px; font-weight:bold; cursor:pointer; margin-bottom:5px;">
                {label}
            </button>
            """
            with cols[idx % 3]:
                st.components.v1.html(pdf_js, height=50)


# --- MODÜL 10: LOKASYON VE EKİPMAN ENVANTER RAPORU ---
def _render_lokasyon_envanter_raporu():
    """📍 Lokasyon Bazlı Ekipman ve Envanter Haritası"""
    st.subheader("📍 Kurumsal Lokasyon & Proses Haritası")
    st.caption("Bina Katı > Lokasyon/Bölüm > Süreç/Alt Hat > Makine/Ekipman Hiyerarşisi")
    
    if not engine:
        st.error("Veritabanı bağlantısı bulunamadı.")
        return
        
    try:
        # 1. Fetch data
        df = run_query("SELECT id, ad, tip, parent_id, sorumlu_departman FROM lokasyonlar WHERE aktif = 1")
    except Exception as e:
        st.error(f"Veri Okuma Hatası: {e}")
        return
        
    if df.empty:
        st.warning("Gösterilecek bir lokasyon veya ekipman tanımı yok.")
        return
        
    id_to_row = {row['id']: row for _, row in df.iterrows()}
    table_rows = []
    
    # Identify leaf nodes to trace upwards
    children_set = set(df['parent_id'].dropna().unique())
    leaf_nodes = df[~df['id'].isin(children_set)]
    
    for _, leaf in leaf_nodes.iterrows():
        path = {'Kat': '-', 'Bölüm': '-', 'Hat': '-', 'Ekipman': '-', 'Sorumlu': 'ÜRETİM DEP. (Varsayılan)'}
        current = leaf
        
        loop_guard = 0
        while current is not None and loop_guard < 10:
            if current['tip'] in path:
                if current['tip'] == 'Ekipman' or current['tip'] == 'Makine':
                     path['Ekipman'] = f"<b>{current['ad']}</b><br>[ID: {current['id']}]"
                elif current['tip'] == 'Kat':
                     path['Kat'] = f"<b>{current['ad']}</b>"
                else:
                     path[current['tip']] = current['ad']
            
            # Capture Department if available at any level
            if pd.notna(current.get('sorumlu_departman')) and current['sorumlu_departman'] != '':
                path['Sorumlu'] = current['sorumlu_departman']
                 
            elif current['tip'] == 'Makine':
                 path['Ekipman'] = f"<b>{current['ad']}</b><br>[ID: {current['id']}]"
                 
            parent_id = current['parent_id']
            if pd.notna(parent_id) and parent_id != 0 and parent_id in id_to_row:
                current = id_to_row[parent_id]
            else:
                current = None
            loop_guard += 1
            
        table_rows.append(path)
        
    if not table_rows:
        st.warning("Hiyerarşi şeması oluşturulamadı.")
        return
        
    report_df = pd.DataFrame(table_rows)
    report_df = report_df.sort_values(by=['Kat', 'Bölüm', 'Hat'])
    
    toplam_bolum = df[df['tip'] == 'Bölüm'].shape[0] if 'Bölüm' in df['tip'].values else 0
    toplam_hat = df[df['tip'] == 'Hat'].shape[0] if 'Hat' in df['tip'].values else 0
    toplam_ekipman = df[(df['tip'] == 'Ekipman') | (df['tip'] == 'Makine')].shape[0]
    
    import time
    from datetime import datetime
    rapor_tarihi = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    html_rows = ""
    for i, row in report_df.iterrows():
        bg_color = ""
        if "KAT -1" in str(row['Kat']).upper(): bg_color = ' style="background-color: #fff3cd;"'
        elif i % 2 == 0: bg_color = ' style="background-color: #f8f8f8;"'
            
        gelecek_faz = '<span style="color:#777; font-style:italic;">🔲 QR: Üretilecek<br>👤 Op: Atanacak</span>'
        if row['Ekipman'] == '-': gelecek_faz = '-'
        
        html_rows += f"""
        <tr{bg_color}>
          <td style="padding: 6px; border: 1px solid #ccc; text-align:center;">{row['Kat']}</td>
          <td style="padding: 6px; border: 1px solid #ccc;">{row['Bölüm']}</td>
          <td style="padding: 6px; border: 1px solid #ccc;">{row['Hat']}</td>
          <td style="padding: 6px; border: 1px solid #ccc;">{row['Ekipman']}</td>
          <td style="padding: 6px; border: 1px solid #ccc;">{row['Sorumlu']}</td>
          <td style="padding: 6px; border: 1px solid #ccc;">{gelecek_faz}</td>
        </tr>
        """
        
    html_kutu = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <title>Lokasyon Bazlı Ekipman Haritası</title>
    </head>
    <body style="font-family:Arial, sans-serif; background:white; margin:0; padding:10px;">
    <div style="border:1px solid #ddd; padding:20px; border-radius:8px;">
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #8B0000; padding-bottom: 10px; margin-bottom: 14px;">
        <div><h1 style="font-size: 16px; color: #1a2744; margin: 0;">LOKASYON BAZLI EKİPMAN VE ENVANTER HARİTASI</h1>
        <p style="margin: 2px 0; font-size: 11px; color: #555;">Doküman No: EKL-KYS-LOK-010</p></div>
        <div style="text-align: right; font-size: 10px; color: #555;">Rev:01 - 15.01.2026<br>Baskı Tarihi: <b>{rapor_tarihi}</b></div>
    </div>
    <div style="display: flex; gap: 12px; margin-bottom: 14px; width: 100%;">
      <div style="flex: 1; padding: 6px 12px; border-radius: 4px; text-align: center; font-weight: bold; font-size: 12px; background: #e3f2fd; color: #1565c0; border: 1px solid #1565c0;">Toplam Bölüm Sayısı: {toplam_bolum}</div>
      <div style="flex: 1; padding: 6px 12px; border-radius: 4px; text-align: center; font-weight: bold; font-size: 12px; background: #e8f5e9; color: #2e7d32; border: 1px solid #2e7d32;">Bölümlerdeki Alt Hatlar: {toplam_hat}</div>
      <div style="flex: 1; padding: 6px 12px; border-radius: 4px; text-align: center; font-weight: bold; font-size: 12px; background: #fff3cd; color: #856404; border: 1px solid #ffeeba;">Tanımlı Makine/Ekipman: {toplam_ekipman}</div>
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px;">
      <thead>
        <tr style="background-color: #1a2744; color: white;">
          <th style="padding: 6px; border: 1px solid #ccc; width: 10%;">Bina Katı</th>
          <th style="padding: 6px; border: 1px solid #ccc; width: 15%;">Lokasyon (Mahal)</th>
          <th style="padding: 6px; border: 1px solid #ccc; width: 20%;">Alt Hat (Süreç)</th>
          <th style="padding: 6px; border: 1px solid #ccc; width: 20%;">Makine / Ekipman</th>
          <th style="padding: 6px; border: 1px solid #ccc; width: 15%;">Sorumlu Departman</th>
          <th style="padding: 6px; border: 1px solid #ccc; width: 20%;">Gelecek Faz (Plan)</th>
        </tr>
      </thead>
      <tbody>
        {html_rows}
      </tbody>
    </table>
    <div style="margin-top: 30px; border-top: 2px solid #1a2744; padding-top: 15px; display: flex; gap: 20px;">
      <div style="flex: 1; border: 1px solid #bbb; border-radius: 4px; padding: 10px 10px 40px 10px; text-align: center; font-size: 10px; color: #555; background: #fafafa;"><b>Üretim Müdürü</b><br>Ad Soyad / İmza</div>
      <div style="flex: 1; border: 1px solid #bbb; border-radius: 4px; padding: 10px 10px 40px 10px; text-align: center; font-size: 10px; color: #555; background: #fafafa;"><b>Kalite Yöneticisi</b><br>Ad Soyad / İmza</div>
      <div style="flex: 1; border: 1px solid #bbb; border-radius: 4px; padding: 10px 10px 40px 10px; text-align: center; font-size: 10px; color: #555; background: #fafafa;"><b>Fabrika Müdürü</b><br>Ad Soyad / İmza</div>
    </div>
    </div>
    </body></html>
    """
    
    st.components.v1.html(html_kutu, height=600, scrolling=True)
    
    import json as _json
    html_json = _json.dumps(html_kutu)
    safe_id = f"btn_lok_{int(time.time())}"
    pdf_js = f'''
    <script>
    function printHarita_{safe_id}() {{
        var html = {html_json};
        var win = window.open('', '_blank');
        win.document.open();
        win.document.write(html);
        win.document.close();
        setTimeout(function() {{ win.print(); }}, 600);
    }}
    </script>
    <button onclick="printHarita_{safe_id}()" style="width:100%; padding:12px; background:#1a2744; color:white; border:none; border-radius:5px; font-size:14px; font-weight:bold; cursor:pointer;">
        🖨️ PDF Oluştur & Yazdır (Envanter Haritası)
    </button>
    '''
    c1, _ = st.columns([1, 1])
    with c1: st.components.v1.html(pdf_js, height=55)

# --- ANA ORKESTRATÖR ---
def render_raporlama_module(engine_param):
    try:
        global engine; engine = engine_param
        st.sidebar.markdown("---")
        st.sidebar.caption("🛠️ Versiyon: **2026.03.09.1750 (Fix-Applied)**")
        if not kullanici_yetkisi_var_mi("📊 Kurumsal Raporlama", "Görüntüle"):
            st.error("🚫 Yetki yok."); st.stop()
        st.title("📊 Kurumsal Raporlar")
        def _reset_repo():
            st.session_state['goster_rapor'] = False

        c1, c2, c3 = st.columns(3)
        bas_tarih = c1.date_input("Başlangıç", get_istanbul_time(), on_change=_reset_repo)
        bit_tarih = c2.date_input("Bitiş", get_istanbul_time(), on_change=_reset_repo)
        rapor_tipi = c3.selectbox("Kategori", [
            "🏭 Üretim ve Verimlilik",
            "🍩 Kalite (KPI) Analizi",
            "📅 Günlük Operasyonel Rapor",
            "🧼 Personel Hijyen Özeti",
            "🧹 Temizlik Takip Raporu",
            "📦 MAP Üretim Raporları",
            "📍 Lokasyon Envanter & Proses Haritası",
            "🗺️ Lokasyon Görsel Şeması",
            "👥 Personel Organizasyon Şeması",
            "❄️ Soğuk Oda İzleme",
            "📈 Soğuk Oda Trend"
        ], on_change=_reset_repo)

        # --- ANAYASA v3.2: MATRİS FİLTRELEME (SAHA VE FONKSİYON) ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Matris Filtreleri")
        
        # 1. Operasyonel Saha Filtresi
        df_sahalar = run_query("SELECT id, bolum_adi FROM ayarlar_bolumler WHERE tur = 'SAHA' AND aktif = 1 ORDER BY sira_no")
        saha_options = {0: "(Tümü)"}
        if not df_sahalar.empty:
            saha_options.update(dict(zip(df_sahalar['id'], df_sahalar['bolum_adi'])))
        
        sel_saha = st.sidebar.selectbox("Operasyonel Saha", options=list(saha_options.keys()), 
                                    format_func=lambda x: saha_options[x], on_change=_reset_repo)
        
        # 2. Fonksiyonel Departman Filtresi
        dept_options = get_department_options_hierarchical()
        sel_dept = st.sidebar.selectbox("Fonksiyonel Departman", options=list(dept_options.keys()), 
                                    format_func=lambda x: dept_options[x], on_change=_reset_repo)

        if st.button("Raporu Oluştur", use_container_width=True):
            st.session_state['goster_rapor'] = True

        if st.session_state.get('goster_rapor', False):
            # Filtreleri args olarak geç
            matrix_filters = {"saha": sel_saha, "dept": sel_dept}
            
            if "MAP" in rapor_tipi: _render_map_raporlari(bas_tarih, bit_tarih)
            elif "Üretim" in rapor_tipi: _render_uretim_raporu(bas_tarih, bit_tarih, matrix_filters)
            elif "KPI" in rapor_tipi: _render_kpi_raporu(bas_tarih, bit_tarih)
            elif "Operasyonel" in rapor_tipi: _render_gunluk_operasyonel_rapor(bas_tarih, matrix_filters)
            elif "Hijyen" in rapor_tipi: _render_hijyen_raporu(bas_tarih, bit_tarih, matrix_filters)
            elif "Temizlik" in rapor_tipi: _render_temizlik_raporu(bas_tarih, bit_tarih)
            elif "Envanter" in rapor_tipi: _render_lokasyon_envanter_raporu()
            elif "Görsel Şeması" in rapor_tipi: _render_lokasyon_haritasi()
            elif "Organizasyon" in rapor_tipi: _render_organizasyon_semasi()
            elif "İzleme" in rapor_tipi: _render_soguk_oda_izleme(bas_tarih, bit_tarih)
            elif "Trend" in rapor_tipi: _render_soguk_oda_trend()
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="RAPOR_MAIN", tip="UI")
