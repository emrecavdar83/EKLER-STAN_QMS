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
    """Vardiya özeti için PDF raporu üretir ve kalıcı arşiv yolunu döner."""
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
    
    # 2. Dosya Yolu ve İsimlendirme (Madde 7: Standart İsimlendirme)
    ts_now = datetime.now(_TZ)
    tarih_str = v['tarih'].replace('-', '')
    fname = f"MAP_RAPOR_{v['makina_no']}_V{v['vardiya_no']}_{tarih_str}_{uuid.uuid4().hex[:6].upper()}.pdf"
    
    # Kalıcı Arşiv Dizini
    data_dir = os.path.join("data", "reports", "map")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    fpath = os.path.join(data_dir, fname)
    
    # 3. PDF Doküman Hazırlığı
    doc = SimpleDocTemplate(fpath, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    
    # Özel Stiller
    style_tit = ParagraphStyle('Tit', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=2, textColor=CLR_NAVY)
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, alignment=1, spaceAfter=20, textColor=colors.grey)
    style_h = ParagraphStyle('H', parent=styles['Heading2'], fontSize=11, spaceBefore=12, spaceAfter=6, color=CLR_NAVY, fontName='Helvetica-Bold')
    style_cell = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=9)
    
    elements = []
    
    # HEADER (LOGO VE BAŞLIK)
    # Not: Logo URL'den çekilemediği durumda sadece metin başlık kullanılır.
    elements.append(Paragraph("E K L E R İ S T A N", style_tit))
    elements.append(Paragraph("MAP MAKİNASI ÜRETİM TAKİP VE VERİMLİLİK RAPORU", ParagraphStyle('SubTit', parent=style_tit, fontSize=12, spaceAfter=5)))
    elements.append(Paragraph(f"Doküman No: EKL-URT-R-MAP-001 | Versiyon: 1.0 | Arşiv Tarihi: {ts_now.strftime('%d.%m.%Y %H:%M')}", style_sub))
    elements.append(Spacer(1, 0.3*cm))
    
    # VARDİYA ÖZET TABLOSU
    v_data = [
        [Paragraph("<b>MAKİNA:</b>", style_cell), v['makina_no'], Paragraph("<b>TARİH:</b>", style_cell), v['tarih']],
        [Paragraph("<b>VARDİYA:</b>", style_cell), f"{v['vardiya_no']}. Vardiya", Paragraph("<b>OPERATÖR:</b>", style_cell), v['operator_adi']],
        [Paragraph("<b>ŞEF:</b>", style_cell), v['vardiya_sefi'] or "-", Paragraph("<b>HEDEF HIZ:</b>", style_cell), f"{v['hedef_hiz_paket_dk']} pk/dk"],
        [Paragraph("<b>BAŞLANGIÇ:</b>", style_cell), v['baslangic_saati'], Paragraph("<b>BİTİŞ:</b>", style_cell), v['bitis_saati'] or "-"],
    ]
    t_v = Table(v_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
    t_v.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), CLR_BG),
        ('BACKGROUND', (2,0), (2,-1), CLR_BG),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_v)
    
    # KPI DASHBOARD (RENKLİ KARTLAR)
    elements.append(Paragraph("⚡ ANAHTAR PERFORMANS GÖSTERGELERİ", style_h))
    kpi_data = [
        ["TOPLAM ÜRETİM", "OEE (Kullanılabilirlik)", "FİRE ORANI", "GERÇEK HIZ"],
        [f"{v['gerceklesen_uretim']} pk", f"%{ozet['kullanilabilirlik_pct']}", f"%{uretim['fire_pct']}", f"{uretim['gercek_hiz']} pk/dk"]
    ]
    t_k = Table(kpi_data, colWidths=[4.5*cm]*4)
    t_k.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.white),
        ('BACKGROUND', (0,0), (-1,0), CLR_NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 13),
        ('BOTTOMPADDING', (0,1), (-1,1), 10),
    ]))
    elements.append(t_k)
    
    # DURUŞ VE ZAMAN ANALİZİ
    elements.append(Paragraph("⏱️ DURUŞ VE ZAMAN ANALİZİ", style_h))
    d_data = [["DURUŞ NEDENİ", "ADET", "TOPLAM SÜRE (DK)", "ORAN (%)"]]
    toplam_durus_dk = ozet.get('toplam_durus_dk', 0)
    for d in duruslar:
        pay = (d['toplam_dk'] / toplam_durus_dk * 100) if toplam_durus_dk > 0 else 0
        d_data.append([d['neden'], d['olay_sayisi'], f"{d['toplam_dk']} dk", f"%{round(pay, 1)}"])
    
    if len(d_data) > 1:
        t_d = Table(d_data, colWidths=[7*cm, 3*cm, 4*cm, 4*cm])
        t_d.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, CLR_BG]),
        ]))
        elements.append(t_d)
    else:
        elements.append(Paragraph("<i>Kayıtlı duruş bulunmamaktadır.</i>", style_cell))
    
    # FİRE DETAYLARI
    elements.append(Paragraph("🔥 FİRE VE KAYIP ANALİZİ", style_h))
    f_data = [["FİRE TİPİ", "MİKTAR (ADET)", "TOPLAM ÜRETİME ORANI (%)"]]
    toplam_uretim = v['gerceklesen_uretim'] or 1
    for f in fireler:
        oran = (f['miktar'] / toplam_uretim * 100) if toplam_uretim > 0 else 0
        f_data.append([f['fire_tipi'], f"{f['miktar']} adet", f"%{round(oran, 2)}"])
        
    if len(f_data) > 1:
        t_f = Table(f_data, colWidths=[8*cm, 5*cm, 5*cm])
        t_f.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), CLR_MAROON),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, CLR_BG]),
        ]))
        elements.append(t_f)
    else:
        elements.append(Paragraph("<i>Kayıtlı fire bulunmamaktadır.</i>", style_cell))

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
