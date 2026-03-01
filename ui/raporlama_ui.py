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
    get_all_sub_department_ids, get_personnel_hierarchy
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

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

# --- HELPERS ---

def _rapor_excel_export(df_display, urun_ozet, bas_tarih, bit_tarih):
    """Excel indirme butonu oluşturur."""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_display.to_excel(writer, index=False, sheet_name='Detaylı Kayıtlar')
            if urun_ozet is not None:
                urun_ozet.to_excel(writer, index=False, sheet_name='Ürün Özeti')
        excel_data = output.getvalue()
        st.download_button(label="📥 Excel Olarak İndir", data=excel_data, file_name=f"uretim_raporu_{bas_tarih}_{bit_tarih}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.caption(f"ℹ️ Excel indirme: openpyxl kütüphanesi gereklidir (pip install openpyxl)")

# --- MODÜL 1: ÜRETİM VE VERİMLİLİK ---
def _render_uretim_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM depo_giris_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("Bu tarihler arasında üretim kaydı bulunamadı.")
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
    rename_map = {'tarih': 'Tarih', 'saat': 'Saat', 'vardiya': 'Vardiya', 'urun': 'Ürün Adı', 'lot_no': 'Lot No', 'miktar': 'Miktar', 'fire': 'Fire', 'kullanici': 'Kaydeden Kullanıcı', 'notlar': 'Notlar'}
    df_display.columns = [rename_map.get(c, c) for c in df_display.columns]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    _rapor_excel_export(df_display, urun_ozet, bas_tarih, bit_tarih)

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

        # Olcum detaylarini notlar alanindan parse et
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

        # Fotograf - dosya varsa base64 olarak gom
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
                foto_html = f'<p><b>STT Etiket Fotografi:</b></p><img src="data:{mime};base64,{foto_b64}" style="max-width:180px;max-height:180px;border:1px solid #ddd;border-radius:4px;margin-top:6px">'
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
    <h1>KALITE KONTROL ANALIZ RAPORU</h1>
    <p>Urun Bazli Olcum Kaydi &nbsp;|&nbsp; EKL-KYS-KPI-001</p>
    <p>Donem: {str(bas_tarih)} / {str(bit_tarih)} &nbsp;|&nbsp; Urun: <b>{urun_sec}</b></p>
  </div>
  <div class="header-meta">Rapor Tarihi:<br><b>{rapor_tarihi}</b></div>
</div>

<div class="ozet-bar">
  <div class="ozet-kart onay">Onaylanan: {len(df_urun[df_urun['karar']=='ONAY'])}</div>
  <div class="ozet-kart red">Reddedilen: {len(df_urun[df_urun['karar']=='RED'])}</div>
  <div class="ozet-kart toplam">Toplam Analiz: {len(df_urun)}</div>
</div>

<div class="filtre-baslik">Tum Kayitlar -- {urun_sec}</div>
{satir_html}

<div class="imza-alani">
  <h3>Imza ve Onay Alani</h3>
  <div class="imza-tablo">
    <div class="imza-kutu"><b>Kalite Kontrol Personeli</b>___________________<br>Ad Soyad / Imza / Tarih</div>
    <div class="imza-kutu"><b>Vardiya Sefi</b>___________________<br>Ad Soyad / Imza / Tarih</div>
    <div class="imza-kutu"><b>Kalite Muduru</b>___________________<br>Ad Soyad / Imza / Tarih</div>
  </div>
</div>

<div class="footer">
  <span>Gizlilik: Dahili Kullanim</span>
  <span>Ekleristan Kalite Yonetim Sistemi v2.0</span>
  <span>Rapor: {rapor_tarihi}</span>
</div>
</body>
</html>"""
    return html


def _render_kpi_raporu(bas_tarih, bit_tarih):
    """Urun bazli KPI raporu: olcum detaylari, personel tam adi, imza, Excel + PDF."""
    import json as _json
    df = run_query(f"SELECT * FROM urun_kpi_kontrol WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("Bu tarih araliginda kalite kaydi bulunamadi.")
        return

    df.columns = [c.lower() for c in df.columns]

    # Personel tam adi haritasi: kullanici_adi -> ad_soyad
    personel_map = {}
    try:
        p_df = run_query("SELECT kullanici_adi, ad_soyad FROM personel WHERE kullanici_adi IS NOT NULL")
        if not p_df.empty:
            p_df.columns = [c.lower() for c in p_df.columns]
            personel_map = dict(zip(p_df['kullanici_adi'].astype(str), p_df['ad_soyad'].astype(str)))
    except Exception:
        pass

    # Ozet metrikler
    onay_s = len(df[df['karar'] == 'ONAY'])
    red_s  = len(df[df['karar'] == 'RED'])
    k1, k2, k3 = st.columns(3)
    k1.success(f"Onaylanan: {onay_s}")
    k2.error(f"Reddedilen: {red_s}")
    k3.info(f"Toplam: {len(df)}")

    st.divider()

    # Urun bazli filtreleme
    urunler = sorted(df['urun'].dropna().unique().tolist())
    urun_sec = st.selectbox("Urun Secin", ["(Tumu)"] + urunler)

    df_urun = df if urun_sec == "(Tumu)" else df[df['urun'] == urun_sec]

    if df_urun.empty:
        st.info("Secilen urun icin kayit yok.")
        return

    # Onizleme tablosu
    with st.expander(f"{urun_sec} -- {len(df_urun)} Kayit (onizleme)", expanded=True):
        goruntu_cols = ['tarih', 'saat', 'vardiya', 'urun',
                        'lot_no' if 'lot_no' in df_urun.columns else 'lot_tlar',
                        'numune_sayisi', 'tat', 'goruntu', 'karar', 'kullanici']
        goruntu_cols = [c for c in goruntu_cols if c in df_urun.columns]
        st.dataframe(df_urun[goruntu_cols], use_container_width=True, hide_index=True)

    st.divider()
    col_excel, col_pdf = st.columns(2)

    # --- EXCEL ---
    try:
        import io
        from datetime import date as _date
        indirme_tarihi = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%Y%m%d')
        urun_dosya = urun_sec.replace(' ', '_').replace('/', '-')[:30]
        dosya_adi = f"KPI_{urun_dosya}_{str(bas_tarih).replace('-','')}_{str(bit_tarih).replace('-','')}_{indirme_tarihi}.xlsx"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_urun.to_excel(writer, index=False, sheet_name='KPI Kayitlar')
        col_excel.download_button(
            label="Excel Olarak Indir",
            data=output.getvalue(),
            file_name=dosya_adi,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except ImportError:
        col_excel.caption("openpyxl yuklu degil")


    # --- PDF: JSON + Blob (UTF-8 uyumlu, atob yok!) ---
    html_rapor = _kpi_html_raporu_olustur(df_urun, urun_sec, bas_tarih, bit_tarih, personel_map)
    html_json = _json.dumps(html_rapor)   # Tum karakterleri ASCII-safe escape eder
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
        Yazdir / PDF Kaydet
    </button>
    """
    with col_pdf:
        st.components.v1.html(pdf_js, height=55)


# --- MODÜL 3: GÜNLÜK OPERASYONEL RAPOR ---
def _render_gunluk_operasyonel_rapor