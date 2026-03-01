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
    df = run_query(f"SELECT * FROM urun_kpi_kontrol WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("Bu tarih aralığında kalite kaydı bulunamadı.")
        return

    df.columns = [c.lower() for c in df.columns]

    personel_map = {}
    try:
        p_df = run_query("SELECT kullanici_adi, ad_soyad FROM personel WHERE kullanici_adi IS NOT NULL")
        if not p_df.empty:
            p_df.columns = [c.lower() for c in p_df.columns]
            personel_map = dict(zip(p_df['kullanici_adi'].astype(str), p_df['ad_soyad'].astype(str)))
    except Exception:
        pass

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

    try:
        indirme_tarihi = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%Y%m%d')
        urun_dosya = urun_sec.replace(' ', '_').replace('/', '-')[:30]
        dosya_adi = f"KPI_{urun_dosya}_{str(bas_tarih).replace('-','')}_{str(bit_tarih).replace('-','')}_{indirme_tarihi}.xlsx"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_urun.to_excel(writer, index=False, sheet_name='KPI Kayıtlar')
        col_excel.download_button(
            label="📥 Excel Olarak İndir",
            data=output.getvalue(),
            file_name=dosya_adi,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except ImportError:
        col_excel.caption("openpyxl yüklü değil")

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
def _render_gunluk_operasyonel_rapor(bas_tarih):
    st.info("📅 Bu rapor belirlediğiniz tarihteki işlemleri özetler.")
    t_str = str(bas_tarih)
    kpi_df = run_query(f"SELECT tarih, saat, urun, karar, notlar, vardiya FROM urun_kpi_kontrol WHERE tarih='{t_str}'")
    uretim_df = run_query(f"SELECT tarih, saat, urun, miktar, vardiya FROM depo_giris_kayitlari WHERE tarih='{t_str}'")
    hijyen_df = run_query(f"SELECT tarih, saat, personel, durum, sebep, aksiyon, vardiya, bolum FROM hijyen_kontrol_kayitlari WHERE tarih='{t_str}'")
    temizlik_df = run_query(f"SELECT tarih, saat, bolum, islem, durum FROM temizlik_kayitlari WHERE tarih='{t_str}'")

    sosts_query = f"SELECT o.oda_adi, m.sicaklik_degeri, m.sapma_var_mi, m.olcum_zamani FROM sicaklik_olcumleri m JOIN soguk_odalar o ON m.oda_id = o.id WHERE {'DATE(m.olcum_zamani)' if 'sqlite' in str(engine.url) else 'm.olcum_zamani::date'} = '{t_str}'"
    sosts_df = run_query(sosts_query)

    v_secim = st.multiselect("Vardiya Seçimi", VARDIYA_LISTESI, default=VARDIYA_LISTESI)
    depts = hijyen_df['bolum'].dropna().unique().tolist() if not hijyen_df.empty else []
    d_secim = st.multiselect("Departman Seçimi", ["Tümü"] + depts, default=["Tümü"])

    if not kpi_df.empty: kpi_df = kpi_df[kpi_df['vardiya'].isin(v_secim)] if 'vardiya' in kpi_df.columns else kpi_df
    if not uretim_df.empty: uretim_df = uretim_df[uretim_df['vardiya'].isin(v_secim)]
    if not hijyen_df.empty:
        hijyen_df = hijyen_df[hijyen_df['vardiya'].isin(v_secim)]
        if "Tümü" not in d_secim: hijyen_df = hijyen_df[hijyen_df['bolum'].isin(d_secim)]

    red_s = len(kpi_df[kpi_df['karar'] == 'RED']) if not kpi_df.empty else 0
    uyg_h = len(hijyen_df[hijyen_df['durum'] != 'Sorun Yok']) if not hijyen_df.empty else 0
    maz_s = len(hijyen_df[hijyen_df['durum'] == 'Gelmedi']) if not hijyen_df.empty else 0
    sapma_s = len(sosts_df[sosts_df['sapma_var_mi'] == 1]) if not sosts_df.empty else 0

    if (red_s + uyg_h + maz_s + sapma_s) > 0:
        st.error(f"🚨 DİKKAT: {red_s} RED | {maz_s} Gelmedi | {uyg_h} Hijyen | {sapma_s} Oda Sapması")
    else:
        st.success("✅ NORMAL ŞARTLAR")

    with st.expander("📋 Detaylı Akış"):
        if not kpi_df.empty: st.write("**KPI:**", kpi_df)
        if not uretim_df.empty: st.write("**Üretim:**", uretim_df)
        if not sosts_df.empty: st.write("**Soğuk Oda:**", sosts_df)
        if not hijyen_df.empty: st.write("**Hijyen:**", hijyen_df)
        if not temizlik_df.empty: st.write("**Temizlik:**", temizlik_df)


# --- MODÜL 4: PERSONEL HİJYEN ÖZETİ ---
def _render_hijyen_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM hijyen_kontrol_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if df.empty:
        st.warning("⚠️ Kayıt bulunamadı."); return
    uygunsuzluk = df[df['durum'] != 'Sorun Yok']
    if not uygunsuzluk.empty:
        st.error(f"⚠️ {len(uygunsuzluk)} Uygunsuzluk / Devamsızlık")
        st.dataframe(uygunsuzluk, use_container_width=True, hide_index=True)
        st.bar_chart(uygunsuzluk['durum'].value_counts())
    else:
        st.success("✅ Sorunsuz")
    with st.expander("📋 Tüm Kayıtlar"):
        st.dataframe(df, use_container_width=True, hide_index=True)


# --- MODÜL 5: TEMİZLİK TAKİP RAPORU ---
def _render_temizlik_raporu(bas_tarih, bit_tarih):
    df = run_query(f"SELECT * FROM temizlik_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
    if not df.empty:
        st.success(f"✅ {len(df)} görev tamamlandı.")
        st.bar_chart(df.groupby('bolum').size())
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Kayıt yok")


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
    loc_df = run_query("SELECT * FROM lokasyonlar WHERE aktif IS TRUE")
    try:
        proses_map = run_query("SELECT lpa.lokasyon_id, pt.ad as proses_adi, pt.ikon FROM lokasyon_proses_atama lpa JOIN proses_tipleri pt ON lpa.proses_tip_id = pt.id WHERE lpa.aktif IS TRUE")
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

def _render_organizasyon_semasi():
    pers_df = get_personnel_hierarchy()
    if pers_df.empty: st.warning("Veri yok"); return
    all_depts = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif = TRUE")
    top = all_depts[all_depts['ana_departman_id'].isna() | (all_depts['ana_departman_id'] == 1)]
    for _, d in top.iterrows():
        if d['id'] != 1: _render_dept_recursive(d['id'], d['bolum_adi'], all_depts, pers_df)


# --- MODÜL 8: SOĞUK ODA İZLEME ---
def _render_soguk_oda_izleme(sel_date):
    """📊 Günlük ölçüm matrisi görünümü."""
    st.subheader("❄️ Günlük Sıcaklık İzleme")
    if not engine:
        st.error("Veritabanı bağlantısı yok.")
        return
    df_matris = get_matrix_data(str(engine.url), sel_date)
    if not df_matris.empty:
        df_matris['saat'] = pd.to_datetime(df_matris['zaman']).dt.strftime('%H:%M')
        status_icons = {'BEKLIYOR': '⏳', 'TAMAMLANDI': '✅', 'GECIKTI': '⚠️', 'ATILDI': '❌'}
        df_matris['display'] = df_matris['durum'].map(status_icons) + " " + df_matris['sicaklik_degeri'].astype(str).replace('nan', '')
        pivot = df_matris.pivot(index='oda_adi', columns='saat', values='display').fillna('—')
        st.dataframe(pivot, use_container_width=True)
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
    df = get_trend_data(str(engine.url), target)
    if not df.empty:
        fig = px.line(df, x='olcum_zamani', y='sicaklik_degeri', title="Sıcaklık Değişim Trendi")
        fig.add_hline(y=float(df['min_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        fig.add_hline(y=float(df['max_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Kayıtlı veri bulunamadı.")


# --- ANA ORKESTRATÖR ---
def render_raporlama_module(engine_param):
    global engine; engine = engine_param
    if not kullanici_yetkisi_var_mi("📊 Kurumsal Raporlama", "Görüntüle"):
        st.error("🚫 Yetki yok."); st.stop()
    st.title("📊 Kurumsal Raporlar")
    c1, c2, c3 = st.columns(3)
    bas_tarih = c1.date_input("Başlangıç", get_istanbul_time() - timedelta(days=7))
    bit_tarih = c2.date_input("Bitiş", get_istanbul_time())
    rapor_tipi = c3.selectbox("Kategori", [
        "🏭 Üretim ve Verimlilik",
        "🍩 Kalite (KPI) Analizi",
        "📅 Günlük Operasyonel Rapor",
        "🧼 Personel Hijyen Özeti",
        "🧹 Temizlik Takip Raporu",
        "📍 Kurumsal Lokasyon & Proses Haritası",
        "👥 Personel Organizasyon Şeması",
        "❄️ Soğuk Oda İzleme",
        "📈 Soğuk Oda Trend"
    ])

    if st.button("Raporu Oluştur", use_container_width=True):
        if "Üretim" in rapor_tipi: _render_uretim_raporu(bas_tarih, bit_tarih)
        elif "KPI" in rapor_tipi: _render_kpi_raporu(bas_tarih, bit_tarih)
        elif "Operasyonel" in rapor_tipi: _render_gunluk_operasyonel_rapor(bas_tarih)
        elif "Hijyen" in rapor_tipi: _render_hijyen_raporu(bas_tarih, bit_tarih)
        elif "Temizlik" in rapor_tipi: _render_temizlik_raporu(bas_tarih, bit_tarih)
        elif "Lokasyon" in rapor_tipi: _render_lokasyon_haritasi()
        elif "Organizasyon" in rapor_tipi: _render_organizasyon_semasi()
        elif "İzleme" in rapor_tipi: _render_soguk_oda_izleme(bas_tarih)
        elif "Trend" in rapor_tipi: _render_soguk_oda_trend()
