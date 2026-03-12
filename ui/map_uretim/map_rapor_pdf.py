"""map_rapor_pdf.py — MAP Modülü PDF Rapor Üreticisi
Anayasa m.2: Arşivlenebilir, benzersiz ID'li kurumsal raporlar.
Format: EKL-URT-R-MAP-001
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

def uret_is_raporu(engine, vardiya_id: int):
    """Vardiya özeti için PDF raporu üretir ve dosya yolunu döner."""
    if not REPORTLAB_AVAIL:
        return None

    # 1. Veri Hazırlama
    aktif = None # db.get_aktif_vardiya(engine) — Biz id ile geliyoruz, direkt fetch edelim.
    with engine.connect() as conn:
        df_v = db._read(conn, "SELECT * FROM map_vardiya WHERE id=:id", {"id": vardiya_id})
        if df_v.empty: return None
        v = df_v.iloc[0].to_dict()
    
    ozet = hesap.hesapla_sure_ozeti(engine, vardiya_id)
    uretim = hesap.hesapla_uretim(engine, vardiya_id)
    duruslar = hesap.hesapla_durus_ozeti(engine, vardiya_id)
    fireler = hesap.hesapla_fire_ozeti(engine, vardiya_id)
    
    # 2. PDF Ayarları
    fname = f"MAP_Rapor_{vardiya_id}_{uuid.uuid4().hex[:6]}.pdf"
    fpath = os.path.join("/tmp", fname)
    doc = SimpleDocTemplate(fpath, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    # Özel Stiller
    style_tit = ParagraphStyle('Tit', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=10)
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, alignment=1, spaceAfter=20)
    style_h = ParagraphStyle('H', parent=styles['Heading2'], fontSize=12, spaceBefore=10, spaceAfter=5, color=colors.navy)
    
    elements = []
    
    # LOGO VE BAŞLIK
    ts = datetime.now(_TZ).strftime("%d.%m.%Y %H:%M")
    elements.append(Paragraph("EKLERİSTAN QMS — MAP MAKİNASI ÜRETİM RAPORU", style_tit))
    elements.append(Paragraph(f"Doküman No: EKL-URT-R-MAP-001 | Rapor Tarihi: {ts}", style_sub))
    elements.append(Spacer(1, 0.5*cm))
    
    # VARDİYA BİLGİLERİ TABLOSU
    v_data = [
        ["Makina:", v['makina_no'], "Tarih:", v['tarih']],
        ["Vardiya:", v['vardiya_no'], "Operatör:", v['operator_adi']],
        ["Sorumlu:", v['vardiya_sefi'] or "-", "Hedef Hız:", f"{v['hedef_hiz_paket_dk']} pk/dk"],
        ["Başlangıç:", v['baslangic_saati'], "Bitiş:", v['bitis_saati'] or "-"],
    ]
    t_v = Table(v_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
    t_v.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
    ]))
    elements.append(t_v)
    elements.append(Spacer(1, 0.8*cm))
    
    # KPI ÖZETİ (Dashboard Kartları gibi)
    elements.append(Paragraph("📊 ANAHTAR PERFORMANS GÖSTERGELERİ (KPI)", style_h))
    kpi_data = [
        ["Üretim Adedi", "Kullanılabilirlik (OEE)", "Fire Oranı", "Gerçek Hız"],
        [f"{v['gerceklesen_uretim']} pk", f"%{ozet['kullanilabilirlik_pct']}", f"%{uretim['fire_pct']}", f"{uretim['gercek_hiz']} pk/dk"]
    ]
    t_k = Table(kpi_data, colWidths=[4*cm]*4)
    t_k.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 14),
    ]))
    elements.append(t_k)
    elements.append(Spacer(1, 0.8*cm))
    
    # DURUŞ ANALİZİ
    elements.append(Paragraph("⏱️ DURUŞ ANALİZİ", style_h))
    d_data = [["Duruş Nedeni", "Olay Sayısı", "Toplam Süre (dk)"]]
    for d in duruslar:
        d_data.append([d['neden'], d['olay_sayisi'], f"{d['toplam_dk']} dk"])
    
    if len(d_data) > 1:
        t_d = Table(d_data, colWidths=[8*cm, 4*cm, 4*cm])
        t_d.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(t_d)
    else:
        elements.append(Paragraph("Duruş kaydı bulunmamaktadır.", styles['Normal']))
    
    elements.append(Spacer(1, 0.8*cm))
    
    # FİRE ANALİZİ
    elements.append(Paragraph("🔥 FİRE ANALİZİ", style_h))
    f_data = [["Fire Tipi", "Miktar (adet)", "Oran (%)"]]
    for f in fireler:
        f_data.append([f['fire_tipi'], f['miktar'], f"%{f['pct']}"])
        
    if len(f_data) > 1:
        t_f = Table(f_data, colWidths=[8*cm, 4*cm, 4*cm])
        t_f.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.darkred),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        elements.append(t_f)
    else:
        elements.append(Paragraph("Fire kaydı bulunmamaktadır.", styles['Normal']))

    # NOTLAR
    if v['notlar']:
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("📝 VARDİYA NOTLARI", style_h))
        elements.append(Paragraph(v['notlar'], styles['Normal']))

    # İMZALAR
    elements.append(Spacer(1, 2*cm))
    sig_data = [
        ["Operatör İmza", "Vardiya Şefi İmza", "Kalite Kontrol İmza"],
        ["", "", ""],
        ["...................", "...................", "..................."]
    ]
    t_s = Table(sig_data, colWidths=[5.3*cm]*3, rowHeights=[0.5*cm, 1.5*cm, 0.5*cm])
    t_s.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    elements.append(t_s)
    
    # FOOTER (13. Adam UUID)
    ruid = f"ARCHIVE_REF: {uuid.uuid4().hex.upper()}"
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"<font size=8 color=grey>{ruid}</font>", styles['Normal']))
    
    # PDF OLUŞTUR
    doc.build(elements)
    return fpath
