"""map_rapor_pdf.py — MAP Modülü PDF Rapor Üreticisi
Anayasa m.2: Arşivlenebilir, benzersiz ID'li kurumsal raporlar.
Format: EKL-URT-R-MAP-001 (Ekleristan Kurumsal Standart)
"""
import os, uuid
from datetime import datetime
import pytz
import pandas as pd
from . import map_db as db
from . import map_hesap as hesap

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm
    REPORTLAB_AVAIL = True
except ImportError:
    REPORTLAB_AVAIL = False

_TZ = pytz.timezone("Europe/Istanbul")

# EKLEİRSTAN KURUMSAL RENKLERİ
CLR_NAVY = colors.HexColor("#1a2744") if REPORTLAB_AVAIL else "#1a2744"
CLR_MAROON = colors.HexColor("#8B0000") if REPORTLAB_AVAIL else "#8B0000"
CLR_BG = colors.HexColor("#f8f9fa") if REPORTLAB_AVAIL else "#f8f9fa"

def _fmt_ts(val):
    """Zaman damgasını HH:MM formatına çevirir (SQL Safe)."""
    if pd.isna(val) or not val: return "-"
    if isinstance(val, str) and len(val) >= 16: return val[11:16]
    try: return val.strftime("%H:%M")
    except: return str(val)

def _map_html_get_data(engine, vardiya_id, df_zaman, df_fire):
    """Raporlar için tüm verileri toplar ve hesaplar."""
    with engine.connect() as conn:
        sql = "SELECT v.*, COALESCE(p.ad_soyad, v.operator_adi) as op_full FROM map_vardiya v LEFT JOIN personel p ON v.operator_adi = p.kullanici_adi WHERE v.id=:id"
        v_df = db._read(conn, sql, {"id": vardiya_id})
        if v_df.empty: return None, None, None, None, None, None
        v = v_df.iloc[0].to_dict(); v['operator_adi'] = v['op_full']
    o = hesap.hesapla_sure_ozeti(engine, vardiya_id, df_zaman=df_zaman, df_vardiya=pd.DataFrame([v]))
    u = hesap.hesapla_uretim(engine, vardiya_id, df_vardiya=pd.DataFrame([v]), df_fire=df_fire, sure_ozeti=o)
    d = hesap.hesapla_durus_ozeti(engine, vardiya_id, df_zaman=df_zaman)
    f = hesap.hesapla_fire_ozeti(engine, vardiya_id, df_fire=df_fire)
    b = db.get_bobinler(engine, vardiya_id)
    return v, o, u, d, f, b

def _map_html_rows_zaman(df_z, ozet):
    """Zaman çizelgesi HTML satırlarını üretir."""
    trs = ""
    for _, r in df_z.iterrows():
        b, f = _fmt_ts(r.get('baslangic_ts')), _fmt_ts(r.get('bitis_ts'))
        trs += f"<tr><td>{r['sira_no']}</td><td>{b}</td><td>{f}</td><td>{r['sure_dk']} dk</td><td>{r['durum']}</td><td>{r['neden'] or '-'}</td></tr>"
    return trs + f"<tr style='background:#eee; font-weight:bold;'><td colspan='3' style='text-align:right;'>TOPLAM:</td><td>{ozet['toplam_vardiya_dk']} dk</td><td colspan='2'></td></tr>"

def _map_html_rows_durus(duruslar, ozet):
    """Duruş analizi HTML satırlarını üretir."""
    trs = ""
    for d in duruslar:
        p = (d['toplam_dk'] / ozet['toplam_durus_dk'] * 100) if ozet['toplam_durus_dk'] > 0 else 0
        trs += f"<tr><td>{d['neden']}</td><td>{d['toplam_dk']} dk</td><td>{d['olay_sayisi']}</td><td>%{round(p,1)}</td></tr>"
    return trs + f"<tr style='background:#eee; font-weight:bold;'><td>TOPLAM:</td><td>{ozet['toplam_durus_dk']} dk</td><td colspan='2'></td></tr>"

def uret_is_raporu_html(engine, vardiya_id, df_zaman=None, df_fire=None):
    """HTML raporu orkestratörü (Anayasa Madde 3 Uyumlu)."""
    from ui.raporlar.report_utils import _generate_base_html
    v, oz, ur, dur, fir, bob = _map_html_get_data(engine, vardiya_id, df_zaman, df_fire)
    if not v: return None
    dz = df_zaman if df_zaman is not None else db.get_zaman_cizelgesi(engine, vardiya_id)
    summary = f'<div class="ozet-kart">Üretim: {ur["gerceklesen_uretim"]} pk</div><div class="ozet-kart">Verimlilik: %{oz["net_kullanilabilirlik_pct"]}</div><div class="ozet-kart red">Fire: {ur["fire_adet"]} pk</div>'
    z_tr, d_tr = _map_html_rows_zaman(dz, oz), _map_html_rows_durus(dur, oz)
    b_tr = "".join([f"<tr><td>{_fmt_ts(r['degisim_ts'])}</td><td>{r['bobin_lot']}</td><td>{r['film_tipi']}</td><td>{r['baslangic_kg']}</td><td>{r['bitis_kg']}</td><td>{r['kullanilan_kg']}</td></tr>" for _, r in bob.iterrows()])
    f_tr = "".join([f"<tr><td>{f['fire_tipi']}</td><td>{f['miktar']}</td><td>%{f['pct']}</td><td>-</td></tr>" for f in fir])
    c = f"""<div style="background:#f9f9f9; padding:10px; border:1px solid #ddd; margin-bottom:15px;"><h3>A. VARDİYA BİLGİLERİ</h3><table><tr><th>Makina</th><td>{v['makina_no']}</td><th>Vardiya</th><td>{v['vardiya_no']}</td><th>Operatör</th><td>{v['operator_adi']}</td></tr><tr><th>Tarih</th><td>{v['tarih']}</td><th>Ürün</th><td colspan="3">{v.get('urun_adi','-')}</td></tr></table></div>
    <h3>C & D. ZAMAN ÇİZELGESİ</h3><table><thead><tr><th>No</th><th>Başl.</th><th>Bitiş</th><th>Dakika</th><th>Durum</th><th>Neden</th></tr></thead><tbody>{z_tr}</tbody></table>
    <div style="display:flex; gap:15px;"><div style="flex:1;"><h3>E. DURUŞ</h3><table><thead><tr><th>Neden</th><th>Dakika</th><th>Olay</th><th>%</th></tr></thead><tbody>{d_tr}</tbody></table></div>
    <div style="flex:1;"><h3>G. FİRE</h3><table><thead><tr><th>Tip</th><th>Miktar</th><th>%</th><th>Not</th></tr></thead><tbody>{f_tr}</tbody></table></div></div>
    <h3>F. BOBİNLER</h3><table><thead><tr><th>Saat</th><th>Lot</th><th>Tip</th><th>Başl.</th><th>Bitiş</th><th>Kull.</th></tr></thead><tbody>{b_tr}</tbody></table>"""
    sigs = '<div class="imza-kutu"><b>Operatör</b><br><br>İmza</div><div class="imza-kutu"><b>Vardiya Şefi</b><br><br>İmza</div><div class="imza-kutu"><b>Kalite Kontrol</b><br><br>İmza</div>'
    return _generate_base_html("MAP MAKİNASI ÜRETİM RAPORU", "EKL-URT-R-MAP-001", f"{v['tarih']} | V{v['vardiya_no']}", summary, c, sigs)

def save_map_report_to_disk(engine, vardiya_id: int):
    """Vardiya kapatıldığında raporu otomatik olarak disk arşivine kaydeder."""
    try:
        html = uret_is_raporu_html(engine, vardiya_id)
        if html:
            with engine.connect() as conn:
                v = db._read(conn, "SELECT makina_no, tarih, vardiya_no FROM map_vardiya WHERE id=:id", {"id": vardiya_id}).iloc[0]
                s_dir = "data/reports/map/archive"; os.makedirs(s_dir, exist_ok=True)
                with open(os.path.join(s_dir, f"MAP_{v['tarih']}_{v['makina_no']}_V{v['vardiya_no']}.html"), "w", encoding="utf-8") as f: f.write(html)
        if REPORTLAB_AVAIL: uret_is_raporu(engine, vardiya_id)
    except Exception as e: print(f"ERROR: Rapor arşivlenemedi: {e}")

def _map_pdf_styles():
    """ReportLab stillerini döndürür."""
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('Tit', fontSize=18, textColor=CLR_NAVY, fontName='Helvetica-Bold'))
    s.add(ParagraphStyle('H', fontSize=11, spaceBefore=8, spaceAfter=4, color=colors.white, backColor=CLR_NAVY, borderPadding=4, fontName='Helvetica-Bold'))
    s.add(ParagraphStyle('Cell', fontSize=8.5, leading=10))
    s.add(ParagraphStyle('KpiVal', fontSize=16, fontName='Helvetica-Bold', alignment=1))
    s.add(ParagraphStyle('KpiLab', fontSize=8, alignment=1, textColor=colors.grey))
    return s

def _map_pdf_add_kpi(els, ozet, uretim, s):
    """KPI bölümlerini ekler."""
    els.append(Paragraph("B. PERFORMANS GÖSTERGELERİ", s['H']))
    r1 = [[Paragraph("Vardiya (dk)", s['KpiLab']), Paragraph(f"{ozet['toplam_vardiya_dk']}", s['KpiVal'])],
          [Paragraph("Çalışma (dk)", s['KpiLab']), Paragraph(f"{ozet['toplam_calisma_dk']}", s['KpiVal'])],
          [Paragraph("Duruş (dk)", s['KpiLab']), Paragraph(f"{ozet['toplam_durus_dk']}", s['KpiVal'])],
          [Paragraph("Kullanım %", s['KpiLab']), Paragraph(f"%{ozet['kullanilabilirlik_pct']}", s['KpiVal'])]]
    r2 = [[Paragraph("Teorik Pk", s['KpiLab']), Paragraph(f"{uretim['teorik_uretim']}", s['KpiVal'])],
          [Paragraph("Gerçekleşen", s['KpiLab']), Paragraph(f"{uretim['gerceklesen_uretim']}", s['KpiVal'])],
          [Paragraph("Fire Pk", s['KpiLab']), Paragraph(f"{uretim['fire_adet']}", s['KpiVal'])],
          [Paragraph("Fire %", s['KpiLab']), Paragraph(f"%{uretim['fire_pct']}", s['KpiVal'])]]
    for row in [r1, r2]:
        t = Table([row], colWidths=[4.7*cm]*4, rowHeights=[1.5*cm])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        els.append(t); els.append(Spacer(1, 0.1*cm))

def uret_is_raporu(engine, vardiya_id: int):
    """Kurumsal PDF raporu (Anayasa Madde 3 Uyumlu)."""
    if not REPORTLAB_AVAIL: return None
    v, oz, ur, dur, fir, bob = _map_html_get_data(engine, vardiya_id, None, None)
    if not v: return None
    fpath = os.path.join("data", "reports", "map", f"MAP_RAPOR_{v['makina_no']}_V{v['vardiya_no']}_{v['tarih'].replace('-','')}.pdf")
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    doc = SimpleDocTemplate(fpath, pagesize=A4, margin=1*cm); s = _map_pdf_styles(); els = []
    
    # Header & Vardiya Info
    els.append(Table([[Paragraph("<b>MAP ÜRETİM RAPORU</b>", s['Tit']), Paragraph("EKLERİSTAN A.Ş.", s['Tit'])]], colWidths=[12*cm, 7*cm]))
    els.append(Spacer(1, 0.5*cm)); els.append(Paragraph("A. VARDİYA BİLGİLERİ", s['H']))
    v_info = [["TARİH", "MAKİNA", "VARDİYA", "OPERATÖR", "ŞEF"], [v['tarih'], v['makina_no'], v['vardiya_no'], v['operator_adi'], v['vardiya_sefi'] or "-"]]
    t_v = Table(v_info, colWidths=[3.8*cm]*5); t_v.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('ALIGN',(0,0),(-1,-1),'CENTER')])); els.append(t_v)
    
    _map_pdf_add_kpi(els, oz, ur, s)
    _map_pdf_add_tables(els, engine, vardiya_id, dur, fir, s)
    
    if v.get('notlar'):
        els.append(Paragraph("📝 PERSONEL NOTLARI", s['H'])); els.append(Paragraph(v['notlar'], s['Cell']))
    
    els.append(Spacer(1, 1*cm))
    sig = [["OPERATÖR", "ŞEF", "KALİTE"], ["\n\n\n", "\n\n\n", "\n\n\n"], [v['operator_adi'], "-", "-"]]
    t_s = Table(sig, colWidths=[6.3*cm]*3); t_s.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('ALIGN',(0,0),(-1,-1),'CENTER')])); els.append(t_s)
    
    doc.build(els); return fpath

def _map_pdf_add_tables(els, engine, vardiya_id, dur, fir, s):
    """Tablo bölümlerini (Zaman, Duruş, Fire) ekler."""
    els.append(Paragraph("C & D. ZAMAN ÇİZELGESİ", s['H']))
    z_data = [["NO", "BAŞL.", "BİTİŞ", "DK", "DURUM", "NEDEN"]]
    for _, r in db.get_zaman_cizelgesi(engine, vardiya_id).iterrows():
        z_data.append([r['sira_no'], _fmt_ts(r['baslangic_ts']), _fmt_ts(r['bitis_ts']), r['sure_dk'], r['durum'], r['neden'] or "-"] )
    t_z = Table(z_data, colWidths=[1*cm, 2.5*cm, 2.5*cm, 1.5*cm, 2.5*cm, 9*cm])
    t_z.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8), ('BACKGROUND', (0,0), (-1,0), CLR_BG)]))
    els.append(t_z)
    
    els.append(Paragraph("E. DURUŞ VE G. FİRE ANALİZİ", s['H']))
    d_data = [["DURUŞ NEDENİ", "DK", "OLAY", "FİRE TİPİ", "ADET"]]
    for i in range(max(len(dur), len(fir))):
        d = dur[i] if i < len(dur) else {"neden":"-","toplam_dk":"-","olay_sayisi":"-"}
        f = fir[i] if i < len(fir) else {"fire_tipi":"-","miktar":"-"}
        d_data.append([d['neden'], d['toplam_dk'], d['olay_sayisi'], f['fire_tipi'], f['miktar']])
    t_mix = Table(d_data, colWidths=[5*cm, 2*cm, 2*cm, 5*cm, 5*cm])
    t_mix.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
    els.append(t_mix)
