"""
EKLERİSTAN QDMS — PDF Üretici Modülü
ReportLab tabanlı, BRCGS/IFS uyumlu yüksek sadakatli PDF çıktısı.
"""
import os
import base64
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas

from static.logo_b64 import LOGO_B64

class QDMSPageNumbers(canvas.Canvas):
    """
    Kanuna uygun Header ve Footer çizen Canvas sınıfı.
    Sağ Blok (Ters Sıra): Baskı Tarihi (Üst) -> Rev (Orta) -> Sayfa (Alt)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._doc_info = {}

    def set_doc_info(self, info):
        self._doc_info = info

    def draw_header_footer(self):
        # Ayarlar
        width, height = self._pagesize
        margin = 15 * mm
        header_y = height - 15 * mm
        
        # --- HEADER SOL: LOGO + ŞİRKET ---
        try:
            logo_data = LOGO_B64.split(",")[1]
            logo_img = BytesIO(base64.b64decode(logo_data))
            # Boyut ölçeklendirme
            self.drawImage(Image(logo_img), margin, header_y - 12*mm, width=35*mm, preserveAspectRatio=True, mask='auto')
        except: pass
        
        self.setFont("Helvetica-Bold", 10)
        self.drawString(margin + 37*mm, header_y - 8*mm, "EKLERİSTAN A.Ş.")
        
        # --- HEADER MERKEZ: FORM ADI + KOD | DÖNEM ---
        self.setFont("Helvetica-Bold", 12)
        title = self._doc_info.get('belge_adi', 'DOKÜMAN')
        self.drawCentredString(width/2, header_y - 5*mm, title)
        
        self.setFont("Helvetica", 9)
        id_period = f"{self._doc_info.get('belge_kodu', '')} | {self._doc_info.get('donem', '')}"
        self.drawCentredString(width/2, header_y - 10*mm, id_period)
        
        # --- HEADER SAĞ (TERS SIRA KANUNU) ---
        # 1. Baskı Tarihi (En Üst)
        # 2. Rev (Orta)
        # 3. Sayfa (En Alt)
        self.setFont("Helvetica", 8)
        baski_t = f"Baskı Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        rev_t = f"Rev: {self._doc_info.get('rev_no', '01')} - {self._doc_info.get('rev_tarihi', '18.03.2026')}"
        sayfa_t = f"Sayfa: {self._pageNumber} / {self._doc_info.get('total_pages', '?')}"
        
        self.drawRightString(width - margin, header_y, baski_t)
        self.drawRightString(width - margin, header_y - 4*mm, rev_t)
        self.drawRightString(width - margin, header_y - 8*mm, sayfa_t)
        
        # Header Alt Çizgisi (2px solid #0d1f3c)
        self.setStrokeColor(colors.HexColor("#0d1f3c"))
        self.setLineWidth(1)
        self.line(margin, header_y - 15*mm, width - margin, header_y - 15*mm)
        
        # --- FOOTER ---
        footer_y = 10 * mm
        self.setFont("Helvetica", 7)
        self.drawString(margin, footer_y, "Dahili Kullanım")
        self.drawCentredString(width/2, footer_y, "EKLERİSTAN Kalite Yönetim Sistemi v3.0")
        self.drawRightString(width - margin, footer_y, f"Baskı: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

def pdf_uret(db_conn, belge_kodu, veri, dosya_yolu=None):
    """
    Ana PDF üretim fonksiyonu.
    """
    if not dosya_yolu:
        dosya_yolu = f"test_{belge_kodu}.pdf"
        
    # Meta veri hazırlığı
    doc_info = {
        'belge_kodu': belge_kodu,
        'belge_adi': veri.get('belge_adi', 'FORMDOK'),
        'donem': veri.get('donem', datetime.now().strftime('%B %Y')),
        'rev_no': veri.get('rev_no', '01'),
        'rev_tarihi': '18.03.2026'
    }
    
    # Sayfa ayarı
    orient = portrait(A4) if veri.get('yonu', 'dikey') == 'dikey' else landscape(A4)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=orient, topMargin=35*mm, bottomMargin=20*mm)
    
    # Stil tanımları
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8)
    
    elements = []
    
    # Tablo Oluşturma
    kolonlar = veri.get('sablon', {}).get('kolon_config', [])
    data = [[Paragraph(k['ad'], header_style) for k in kolonlar]]
    
    # Veri satırlarını ekle
    for satir in veri.get('satirlar', []):
        row = []
        for k in kolonlar:
            val = str(satir.get(k['tip'], satir.get(k['ad'].lower(), '')))
            # Durum Badge Mantığı
            if k['tip'] == 'durum_badge':
                if val.lower() == 'uygun':
                    p_style = ParagraphStyle('GreenStyle', parent=cell_style, textColor=colors.green)
                else:
                    p_style = ParagraphStyle('RedStyle', parent=cell_style, textColor=colors.red)
                row.append(Paragraph(val, p_style))
            else:
                row.append(Paragraph(val, cell_style))
        data.append(row)
    
    # Tablo Stili
    t_widths = [ (w['genislik_yuzde'] * (orient[0] - 30*mm) / 100) for w in kolonlar]
    t = Table(data, colWidths=t_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t)
    
    # Render
    def my_header_footer(canvas, doc):
        canvas.set_doc_info(doc_info)
        canvas.draw_header_footer()
        
    doc.build(elements, onFirstPage=my_header_footer, onLaterPages=my_header_footer, canvasmaker=QDMSPageNumbers)
    
    # Kayıt
    pdf_out = buffer.getvalue()
    with open(dosya_yolu, "wb") as f:
        f.write(pdf_out)
    
    return dosya_yolu

def logo_base64_getir():
    return LOGO_B64
