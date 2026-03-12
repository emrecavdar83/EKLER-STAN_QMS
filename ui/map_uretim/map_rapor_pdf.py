"""map_rapor_pdf.py — MAP Modülü PDF Rapor Üreticisi
Anayasa m.2: Arşivlenebilir, benzersiz ID'li kurumsal raporlar.
Format: EKL-URT-R-MAP-001 (Ekleristan Kurumsal Standart)
"""
import os, uuid
from datetime import datetime
import pytz
from . import map_db as db
from . import map_hesap as hesap

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.units import cm
    REPORTLAB_AVAIL = True
except ImportError:
    REPORTLAB_AVAIL = False

_TZ = pytz.timezone("Europe/Istanbul")

# EKLEİRSTAN KURUMSAL RENKLERİ
CLR_NAVY = colors.HexColor("#1a2744")
CLR_MAROON = colors.HexColor("#8B0000")
CLR_BG = colors.HexColor("#f8f9fa")

def uret_is_raporu(engine, vardiya_id: int):
    """Vardiya özeti için GÖRSEL FORMATLI PDF raporu üretir.
    Format: EKL-URT-R-MAP-001 (Revize)
    """
    if not REPORTLAB_AVAIL:
        return None

    # 1. Veri Hazırlama
    with engine.connect() as conn:
        df_v = db._read(conn, "SELECT * FROM map_vardiya WHERE id=:id", {"id": vardiya_id})
        if df_v.empty: return None
        v = df_v.iloc[0].to_dict()
    
    ozet = hesap.hesapla_sure_ozeti(engine, vardiya_id)
    uretim = hesap.hesapla_uretim(engine, vardiya_id)
    duruslar = hesap.hesapla_durus_ozeti(engine, vardiya_id)
    fireler = hesap.hesapla_fire_ozeti(engine, vardiya_id)
    
    # 2. Dosya Yolu ve İsimlendirme
    ts_now = datetime.now(_TZ)
    tarih_str = v['tarih'].replace('-', '')
    fname = f"MAP_RAPOR_{v['makina_no']}_V{v['vardiya_no']}_{tarih_str}.pdf"
    data_dir = os.path.join("data", "reports", "map")
    os.makedirs(data_dir, exist_ok=True)
    fpath = os.path.join(data_dir, fname)
    
    # 3. PDF Doküman Hazırlığı
    doc = SimpleDocTemplate(fpath, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    
    # Gelişmiş Stiller
    style_tit = ParagraphStyle('Tit', fontSize=18, alignment=0, textColor=CLR_NAVY, fontName='Helvetica-Bold')
    style_sub = ParagraphStyle('Sub', fontSize=9, alignment=2, textColor=colors.grey)
    style_h = ParagraphStyle('H', fontSize=11, spaceBefore=8, spaceAfter=4, color=colors.white, backColor=CLR_NAVY, 
                            borderPadding=4, fontName='Helvetica-Bold', leftIndent=0)
    style_cell = ParagraphStyle('Cell', fontSize=8.5, leading=10)
    style_kpi_val = ParagraphStyle('KpiVal', fontSize=16, fontName='Helvetica-Bold', alignment=1)
    style_kpi_lab = ParagraphStyle('KpiLab', fontSize=8, alignment=1, textColor=colors.grey)

    elements = []
    
    # HEADER (A Bölümü öncesi üst bilgi)
    header_data = [
        [Paragraph(f"<b>MAP MAKİNASI ÜRETİM İŞ RAPORU</b>", style_tit), Paragraph("EKLERİSTAN A.Ş.", ParagraphStyle('Comp', fontSize=12, alignment=2, fontName='Helvetica-Bold'))],
        [Paragraph(f"Rapor No: EKL-MAP-{v['id']} | Tarih: {v['tarih']} | Makina: {v['makina_no']} | {v['vardiya_no']}. Vardiya", style_cell), Paragraph("EKL-URT-R-MAP-001 | Sayfa 1/1", style_sub)]
    ]
    t_h = Table(header_data, colWidths=[12*cm, 7*cm])
    t_h.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
    elements.append(t_h)
    elements.append(Spacer(1, 0.2*cm))

    # A. VARDİYA BİLGİLERİ
    elements.append(Paragraph("A. VARDİYA BİLGİLERİ", style_h))
    v_info = [
        ["TARİH", "MAKİNA NO", "VARDİYA", "OPERATÖR", "VARDİYA ŞEFİ", "KALİTE KONTROL"],
        [v['tarih'], v['makina_no'], f"{v['vardiya_no']}. Vardiya", v['operator_adi'], v['vardiya_sefi'] or "-", "-"]
    ]
    t_a = Table(v_info, colWidths=[3.1*cm]*6)
    t_a.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), CLR_BG),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_a)

    # B. PERFORMANS GÖSTERGELERİ (KPI Kartları)
    elements.append(Paragraph("B. PERFORMANS GÖSTERGELERİ (Otomatik Hesaplanan)", style_h))
    kpi_row1 = [
        [Paragraph("Toplam Vardiya", style_kpi_lab), Paragraph(f"{ozet['toplam_vardiya_dk']}", style_kpi_val), Paragraph("Dakika", style_kpi_lab)],
        [Paragraph("Net Çalışma", style_kpi_lab), Paragraph(f"{ozet['toplam_calisma_dk']}", style_kpi_val), Paragraph("Dakika", style_kpi_lab)],
        [Paragraph("Toplam Duruş", style_kpi_lab), Paragraph(f"{ozet['toplam_durus_dk']}", style_kpi_val), Paragraph("Dakika", style_kpi_lab)],
        [Paragraph("Kullanılabilirlik", style_kpi_lab), Paragraph(f"%{ozet['kullanilabilirlik_pct']}", style_kpi_val), Paragraph("(Mola Dahil)", style_kpi_lab)],
        [Paragraph("Net Kullanılabilirlik", style_kpi_lab), Paragraph(f"%{ozet['net_kullanilabilirlik_pct']}", style_kpi_val), Paragraph("(OEE Temelli)", style_kpi_lab)]
    ]
    kpi_row2 = [
        [Paragraph("Teorik Üretim", style_kpi_lab), Paragraph(f"{uretim['teorik_uretim']}", style_kpi_val), Paragraph("Paket", style_kpi_lab)],
        [Paragraph("Gerçekleşen", style_kpi_lab), Paragraph(f"{uretim['gerceklesen_uretim']}", style_kpi_val), Paragraph("Paket", style_kpi_lab)],
        [Paragraph("Fire Miktarı", style_kpi_lab), Paragraph(f"{uretim['fire_adet']}", style_kpi_val), Paragraph("Paket", style_kpi_lab)],
        [Paragraph("Fire Oranı", style_kpi_lab), Paragraph(f"%{uretim['fire_pct']}", style_kpi_val), Paragraph("(Toplam Paket)", style_kpi_lab)],
        [Paragraph("Gerçek Hız", style_kpi_lab), Paragraph(f"{uretim['gercek_hiz']}", style_kpi_val), Paragraph("Paket / Dk", style_kpi_lab)]
    ]
    
    for row in [kpi_row1, kpi_row2]:
        t_k = Table([row], colWidths=[3.7*cm]*5, rowHeights=[1.8*cm])
        t_k.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.white),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (0,0), colors.aliceblue),
            ('BACKGROUND', (1,0), (1,0), colors.mintcream),
            ('BACKGROUND', (2,0), (2,0), colors.whitesmoke),
            ('BACKGROUND', (3,0), (3,0), colors.lightyellow),
            ('BACKGROUND', (4,0), (4,0), colors.honeydew if row==kpi_row1 else colors.seashell),
        ]))
        elements.append(t_k)
        elements.append(Spacer(1, 0.1*cm))

    # C & D. ZAMAN ÇİZELGESİ
    elements.append(Paragraph("C & D. ÇALIŞMA & DURUŞ ZAMAN ÇİZELGESİ", style_h))
    df_z = db.get_zaman_cizelgesi(engine, vardiya_id)
    z_data = [["NO", "BAŞLANGIÇ", "BİTİŞ", "SÜRE (dk)", "DURUM", "NEDEN"]]
    for _, r in df_z.iterrows():
        b = r['baslangic_ts'][11:16]
        bit = r['bitis_ts'][11:16] if r['bitis_ts'] else "-"
        z_data.append([r['sira_no'], b, bit, r['sure_dk'], r['durum'], r['neden'] or "-"])
    
    t_z = Table(z_data, colWidths=[1*cm, 3*cm, 3*cm, 2.5*cm, 3*cm, 6*cm])
    t_z.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), CLR_BG),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke])
    ]))
    elements.append(t_z)

    # E. DURUŞ ANALİZİ
    elements.append(Paragraph("E. DURUŞ ANALİZİ", style_h))
    col_l, col_r = 9*cm, 10*cm
    d_data = [["NEDEN", "SÜRE (dk)", "OLAY", "AĞIRLIK (%)"]]
    for d in duruslar:
        pay = (d['toplam_dk'] / ozet['toplam_durus_dk'] * 100) if ozet['toplam_durus_dk'] > 0 else 0
        d_data.append([d['neden'], d['toplam_dk'], d['olay_sayisi'], f"%{round(pay,1)}"])
    
    t_e = Table(d_data, colWidths=[4*cm, 2*cm, 1.5*cm, 1.5*cm])
    t_e.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke)
    ]))
    
    # Raporlab ile Pasta Grafik eklenebilir ama şimdilik tablo yeterli.
    elements.append(t_e)

    # F. BOBİN DEĞİŞİM KAYDI (KG BAZLI)
    elements.append(Paragraph("F. BOBİN DEĞİŞİM KAYDI (KG)", style_h))
    df_b = db.get_bobinler(engine, vardiya_id)
    b_data = [["SAAT", "LOT NO", "FİLM TİPİ", "BAŞLANGIÇ (KG)", "BİTİŞ (KG)", "KULLANILAN"]]
    for _, r in df_b.iterrows():
        b_data.append([r['degisim_ts'][11:16], r['bobin_lot'], r.get('film_tipi','-'), r.get('baslangic_kg',0), r.get('bitis_kg',0), r.get('kullanilan_kg',0)])
    
    t_b = Table(b_data, colWidths=[2.5*cm, 3.5*cm, 3*cm, 3*cm, 3*cm, 3.5*cm])
    t_b.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke)
    ]))
    elements.append(t_b)

    # G. FİRE ANALİZİ
    elements.append(Paragraph("G. FİRE ANALİZİ", style_h))
    f_data = [["FİRE TİPİ", "MİKTAR (adet)", "ORAN (%)", "AÇIKLAMA"]]
    for f in fireler:
        f_data.append([f['fire_tipi'], f['miktar'], f"{f['pct']}%", "-"])
    
    t_g = Table(f_data, colWidths=[6*cm, 4*cm, 3*cm, 5.5*cm])
    t_g.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke)
    ]))
    elements.append(t_g)

    # H. ONAY & İMZA
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("H. ONAY & İMZA", style_h))
    sig = [["OPERATÖR", "VARDİYA ŞEFİ", "KALİTE KONTROL"], ["\n\n", "\n\n", "\n\n"], [v['operator_adi'], v['vardiya_sefi'] or "-", "-"]]
    t_s = Table(sig, colWidths=[6.2*cm]*3)
    t_s.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    elements.append(t_s)

    doc.build(elements)
    return fpath

    # NOTLAR VE ONAY
    if v['notlar']:
        elements.append(Spacer(1, 0.4*cm))
        elements.append(Paragraph("📝 VARDİYA PERSONEL NOTLARI", style_h))
        elements.append(Paragraph(v['notlar'], ParagraphStyle('Note', parent=styles['Normal'], leftIndent=10, italic=True)))

    # İMZA BÖLÜMÜ
    elements.append(Spacer(1, 1.5*cm))
    sig_data = [
        ["OPERATÖR İMZA", "VARDİYA ŞEFİ İMZA", "KALİTE KONTROL İMZA"],
        ["", "", ""],
        ["..............................", "..............................", ".............................."]
    ]
    t_s = Table(sig_data, colWidths=[6*cm]*3, rowHeights=[0.5*cm, 1.5*cm, 0.5*cm])
    t_s.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
    ]))
    elements.append(t_s)
    
    # FOOTER (ARŞİV KİMLİĞİ)
    ruid = f"REF_ID: {uuid.uuid4().hex.upper()} | ARCHIVE_PATH: {fpath}"
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"<font size=7 color=grey>{ruid}</font>", ParagraphStyle('Foot', parent=styles['Normal'], alignment=1)))
    
    # PDF OLUŞTUR
    doc.build(elements)
    
    # Eğer /tmp dışında bir yere yazıyorsak ve Streamlit'ten indirme yapılacaksa 
    # dosya yolunu döneriz.
    return fpath
