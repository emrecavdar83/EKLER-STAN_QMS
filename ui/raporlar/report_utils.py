import streamlit as st
import pandas as pd
from datetime import datetime
import io
import pytz
import time
from logic.translation_logic import translate_columns, get_tr_label

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

def _rapor_excel_export(st, df_main, df_summary=None, report_name="Rapor", start_date=None, end_date=None):
    """
    Merkezi Excel İhracat Fonksiyonu.
    Anayasa Madde 7 Uyarınca: Standart Dosya İsimlendirmesi ve Çoklu Tablo Desteği.
    """
    try:
        # İndirme Tarihi (Bugün)
        download_tarih = get_istanbul_time().strftime('%Y%m%d')
        
        # Dosya İsim Standardı: RAPOR_ADI_BAS_BIT_INDIRMETARIHI
        safe_name = report_name.replace(' ', '_').replace('/', '-').upper()
        start_str = str(start_date).replace('-', '') if start_date else ""
        end_str = str(end_date).replace('-', '') if end_date else ""
        file_name = f"{safe_name}_{start_str}_{end_str}_{download_tarih}.xlsx"

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Ana Veri (v8.5: Türkçeleştirme Uygulanıyor)
            df_main_tr = translate_columns(df_main)
            df_main_tr.to_excel(writer, index=False, sheet_name='Kayıtlar')
            # Varsa Özet Veri
            if df_summary is not None and not df_summary.empty:
                df_summary_tr = translate_columns(df_summary)
                df_summary_tr.to_excel(writer, index=False, sheet_name='Özet')
                
        excel_data = output.getvalue()
        st.download_button(
            label=f"📥 Excel ({report_name}) İndir",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            key=f"dl_{safe_name}_{time.time()}"
        )
    except Exception as e:
        st.error(f"Excel oluşturma hatası: {e}")

def _get_personnel_display_map(run_query, engine=None):
    """
    Kullanici_adi -> 'Ad Soyad (Görev) [Saha]' eşleşmesini döndürür.
    Anayasa Madde 4: Dinamik veri çekme ve Matris Kimliği.
    """
    try:
        # v6.8.9: Targeted Source - Reports now include all personnel data
        query = """
            SELECT p.kullanici_adi, p.ad_soyad, p.gorev, b.ad as saha_adi
            FROM tum_personel p
            LEFT JOIN qms_departmanlar b ON p.operasyonel_bolum_id = b.id
            WHERE p.ad_soyad IS NOT NULL AND (p.durum = 'AKTİF' OR p.durum = 'AKTIF')
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
    except Exception:
        return {}

def _generate_base_html(title, doc_no, period, summary_cards, content, signatures, rev_no="02", rev_date="15.01.2026"):
    rapor_tarihi = get_istanbul_time().strftime('%d.%m.%Y %H:%M')
    LOGO_URL = "https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png"
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 10mm; }}
  @media print {{ 
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; margin: 0; }}
    .no-print {{ display: none; }}
  }}
  body {{ font-family: Arial, sans-serif; font-size: 11px; color: #333; background: white; margin: 0; padding: 10px; }}
  
  /* ISO Antetli Header Tablo Tasarımı */
  .report-header-table {{ 
    width: 100%; 
    border-collapse: collapse; 
    margin-bottom: 20px; 
    border: 2px solid #1a2744;
  }}
  .report-header-table td {{ 
    border: 1px solid #1a2744; 
    padding: 8px; 
    vertical-align: middle; 
  }}
  .logo-cell {{ 
    width: 20%; 
    text-align: center; 
  }}
  .logo-cell img {{ 
    height: 45px; 
  }}
  .title-cell {{ 
    width: 50%; 
    text-align: center; 
  }}
  .title-cell h1 {{ 
    font-size: 14px; 
    color: #1a2744; 
    margin: 0; 
    text-transform: uppercase; 
    font-weight: bold;
  }}
  .title-cell p {{ 
    margin: 4px 0 0 0; 
    font-size: 10px; 
    color: #555; 
  }}
  .meta-cell {{ 
    width: 30%; 
    font-size: 9px; 
    color: #333; 
    line-height: 1.4;
  }}

  .ozet-bar {{ display: flex; gap: 12px; margin-bottom: 14px; width: 100%; }}
  .ozet-kart {{ flex: 1; padding: 6px 12px; border-radius: 4px; text-align: center; font-weight: bold; font-size: 12px; }}
  .onay {{ background: #e8f5e9; color: #2e7d32; border: 1px solid #2e7d32; }}
  .red {{ background: #ffebee; color: #b71c1c; border: 1px solid #b71c1c; }}
  .toplam {{ background: #e3f2fd; color: #1565c0; border: 1px solid #1565c0; }}
  table:not(.report-header-table) {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; }}
  table:not(.report-header-table) th {{ background-color: #1a2744; color: white; padding: 6px; text-align: left; border: 1px solid #ccc; }}
  table:not(.report-header-table) td {{ padding: 6px; border: 1px solid #ccc; }}
  table:not(.report-header-table) tr:nth-child(even) {{ background-color: #f8f8f8; }}
  .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: bold; display: inline-block; text-align: center; }}
  .bg-green {{ background-color: #2e7d32; color: white; }}
  .bg-red {{ background-color: #b71c1c; color: white; }}
  .imza-alani {{ margin-top: 30px; page-break-inside: avoid; }}
  .imza-tablo {{ display: flex; gap: 20px; }}
  .imza-kutu {{ flex: 1; border: 1px solid #bbb; border-radius: 4px; padding: 10px 10px 40px 10px; text-align: center; font-size: 10px; color: #555; background: #fafafa; }}
  .imza-kutu b {{ display: block; color: #1a2744; margin-bottom: 8px; font-size: 11px; }}
  .footer {{ margin-top: 20px; border-top: 1px solid #ccc; padding-top: 8px; display: flex; justify-content: space-between; font-size: 9px; color: #777; }}
  .brc-warning {{ font-weight: bold; color: #b71c1c; font-size: 10px; text-align: center; margin-bottom: 5px; }}
</style>
</head>
<body>
<table class="report-header-table">
  <tr>
    <td class="logo-cell" rowspan="3"><img src="{LOGO_URL}" alt="Logo"></td>
    <td class="title-cell" rowspan="3">
      <h1>{title}</h1>
      <p>Dönem: <b>{period}</b></p>
    </td>
    <td class="meta-cell"><b>Doküman No:</b> {doc_no}</td>
  </tr>
  <tr>
    <td class="meta-cell"><b>Revizyon:</b> {rev_no} / {rev_date}</td>
  </tr>
  <tr>
    <td class="meta-cell"><b>Baskı Tarihi:</b> {rapor_tarihi}</td>
  </tr>
</table>
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
  <div>Ekleristan QMS v5.0 - Dijital Kayıt Sistemi</div>
  <div>Elektronik ortamda üretilmiştir. Islak imza gerektirmez.</div>
</div>
</body>
</html>"""
