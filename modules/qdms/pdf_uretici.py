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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.pdfgen import canvas
from constants import get_position_icon, get_position_name

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
    
    if veri.get('belge_tipi') == 'GK':
        return _gk_pdf_render(elements, header_style, cell_style, veri, orient)

    # --- BRC/IFS/FSSC 22000 BÖLÜMLERİ (PR, TL, SO vb.) ---
    def _add_section(title, content):
        if content and len(str(content).strip()) > 1:
            elements.append(Paragraph(f"<b>{title}</b>", header_style))
            elements.append(Spacer(1, 2*mm))
            elements.append(Paragraph(str(content).replace('\n', '<br/>'), cell_style))
            elements.append(Spacer(1, 5*mm))

    _add_section("1. AMAÇ (PURPOSE)", veri.get('amac'))
    _add_section("2. KAPSAM VE SORUMLULUK (SCOPE & RESPONSIBILITY)", veri.get('kapsam'))
    _add_section("3. TANIMLAR VE KISALTMALAR (DEFINITIONS)", veri.get('tanimlar'))
    
    # 4. UYGULAMA (APPLICATION)
    icerik = veri.get('icerik', '')
    if icerik:
        elements.append(Paragraph("<b>4. UYGULAMA (APPLICATION)</b>", header_style))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(str(icerik).replace('\n', '<br/>'), cell_style))
        elements.append(Spacer(1, 5*mm))

    # 5. TABLO VERİSİ (Varsa)
    kolonlar = veri.get('sablon', {}).get('kolon_config', [])
    if kolonlar:
        if not icerik: # Uygulama metni yoksa tabloyu uygulama olarak gösterir
             elements.append(Paragraph("<b>4. UYGULAMA / KAYIT TABLOSU</b>", header_style))
             elements.append(Spacer(1, 2*mm))
             
        data = [[Paragraph(k['ad'], header_style) for k in kolonlar]]
        for satir in veri.get('satirlar', []):
            row = []
            for k in kolonlar:
                val = str(satir.get(k['tip'], satir.get(k['ad'].lower(), '')))
                if k['tip'] == 'durum_badge':
                    col_color = colors.green if val.lower() == 'uygun' else colors.red
                    p_style = ParagraphStyle('BadgeStyle', parent=cell_style, textColor=col_color)
                    row.append(Paragraph(val, p_style))
                else: row.append(Paragraph(val, cell_style))
            data.append(row)
        
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
        elements.append(Spacer(1, 5*mm))

    _add_section("5. İLGİLİ DOKÜMANLAR (RELATED DOCUMENTS)", veri.get('dokumanlar'))
    
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

def _gk_pdf_render(elements, header_style, cell_style, veri, orient):
    """Görev Kartı için 10 bölümlü özel PDF render motoru (v3.5 BRCGS Uyumlu)."""
    def _add_h(txt): 
        elements.append(Paragraph(f"<b>{txt}</b>", header_style))
        elements.append(Spacer(1, 2*mm))
    
    # 1. Belge Kimliği
    _add_h("1. BELGE KİMLİĞİ")
    k_data = [
        ["Belge Kodu:", veri.get('belge_kodu',''), "Revizyon No:", veri.get('rev_no','1')],
        ["Yayım Tarihi:", veri.get('yayim_tarihi','-'), "Durum:", veri.get('durum','Aktif')]
    ]
    t_kim = Table(k_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
    t_kim.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTSIZE',(0,0),(-1,-1),8)]))
    elements.append(t_kim)
    elements.append(Spacer(1, 5*mm))

    # 2. Pozisyon Profili
    _add_h("2. POZİSYON PROFİLİ")
    p_data = [
        ["Pozisyon Adı:", veri.get('pozisyon_adi',''), "Departman:", veri.get('departman','')],
        ["Bağlı Pozisyon:", veri.get('bagli_pozisyon',''), "Vekâlet Eden:", veri.get('vekalet_eden','')],
        ["Zone:", (veri.get('zone','') or '').upper(), "Vardiya:", veri.get('vardiya_turu','')]
    ]
    t_prof = Table(p_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
    t_prof.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTSIZE',(0,0),(-1,-1),8)]))
    elements.append(t_prof)
    elements.append(Spacer(1, 5*mm))

    # 3. Görev Özeti
    _add_h("3. GÖREV ÖZETİ")
    elements.append(Paragraph(veri.get('gorev_ozeti','') or '-', cell_style))
    elements.append(Spacer(1, 5*mm))

    # 4. Sorumluluk Alanları (v3.7: BRCGS Ideal Layout)
    _add_h("4. SORUMLULUK ALANLARI")
    eb_style = ParagraphStyle('EB', parent=cell_style, fontSize=8, leftIndent=5*mm, textColor=colors.grey, fontName='Helvetica-Oblique')
    
    mapping = [
        ('personel', '4.1 PERSONEL YÖNETİMİ'),
        ('operasyon', '4.2 OPERASYONEL GEREKLİLİKLER'),
        ('gida_guvenligi', '4.3 GIDA GÜVENLİĞİ VE KALİTE'),
        ('isg', '4.4 İŞ SAĞLIĞI VE GÜVENLİĞİ'),
        ('cevre', '4.5 ÇEVRE GEREKLİLİKLERİ')
    ]
    
    for d_tip, label in mapping:
        kat_sor = [s for s in veri.get('sorumluluklar', []) if s.get('disiplin_tipi') == d_tip]
        if kat_sor:
            from reportlab.platypus import CondPageBreak
            elements.append(CondPageBreak(25*mm)) # Sayfa sonu koruması
            elements.append(Paragraph(f"<b>{label}:</b>", cell_style))
            for s in kat_sor:
                elements.append(Paragraph(f"• {s['sorumluluk']}", cell_style))
                if s.get('etkilesim_birimleri'):
                    e_units = s['etkilesim_birimleri'].replace(',', ', ')
                    elements.append(Paragraph(f"<i>Süreçler Arası Etkileşim: {e_units}</i>", eb_style))
            elements.append(Spacer(1, 4*mm))
    
    if not veri.get('sorumluluklar'): 
        elements.append(Paragraph("- Henüz görev tanımı sorumlulukları girilmemiştir -", cell_style))
    elements.append(Spacer(1, 5*mm))

    # 5. Yetki Sınırları
    _add_h("5. YETKİ SINIRLARI")
    elements.append(Paragraph(f"<b>Finansal Yetki:</b> {veri.get('finansal_yetki_tl','0')} TL", cell_style))
    elements.append(Paragraph(f"<b>İmza Yetkisi:</b> {veri.get('imza_yetkisi','')}", cell_style))
    if veri.get('vekalet_kosullari'):
        elements.append(Paragraph(f"<b>Vekâlet Devir Koşulları:</b> {veri.get('vekalet_kosullari')}", cell_style))
    elements.append(Spacer(1, 5*mm))

    # 6. Süreçler Arası Etkileşim (RACI)
    _add_h("6. SÜREÇLER ARASI ETKİLEŞİM")
    e_data = [["Taraf / Departman", "Konu / Süreç", "Yöntem", "RACI Rolü"]]
    for e in veri.get('etkilesimler', []):
        e_data.append([e['taraf'], e['konu'], e.get('siklik','-'), e['raci_rol']])
    if len(e_data) == 1: e_data.append(["-","-","-","-"])
    t_e = Table(e_data, colWidths=[35*mm, 85*mm, 35*mm, 25*mm])
    t_e.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
        ('FONTSIZE',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),3),
        ('RIGHTPADDING',(0,0),(-1,-1),3),
    ]))
    elements.append(t_e)
    elements.append(Spacer(1, 5*mm))

    # 7. Periyodik Görev Listesi
    _add_h("7. PERİYODİK GÖREV LİSTESİ")
    g_data = [["Görev", "Periyot", "Talimat", "Standart"]]
    for g in veri.get('periyodik_gorevler', []):
        g_data.append([g['gorev_adi'], g['periyot'], g.get('talimat_kodu',''), g.get('sertifikasyon_maddesi','')])
    if len(g_data) == 1: g_data.append(["-","-","-","-"])
    t_g = Table(g_data, colWidths=[70*mm, 25*mm, 45*mm, 40*mm])
    t_g.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),('FONTSIZE',(0,0),(-1,-1),8)]))
    elements.append(t_g)
    elements.append(Spacer(1, 5*mm))

    # 8. Nitelik ve Yetkinlik
    _add_h("8. NİTELİK VE YETKİNLİK")
    elements.append(Paragraph(f"<b>Eğitim Gereksinimi:</b> {veri.get('min_egitim','-')}", cell_style))
    elements.append(Paragraph(f"<b>Asgari Deneyim:</b> {veri.get('min_deneyim_yil','0')} yıl", cell_style))
    try:
        serts = json.loads(veri.get('zorunlu_sertifikalar','[]')) if isinstance(veri.get('zorunlu_sertifikalar'), str) else veri.get('zorunlu_sertifikalar',[])
        if serts: elements.append(Paragraph(f"<b>Zorunlu Sertifikalar:</b> {', '.join(serts)}", cell_style))
    except: pass
    elements.append(Spacer(1, 5*mm))

    # 9. Performans Göstergeleri (KPI)
    _add_h("9. PERFORMANS GÖSTERGELERİ (KPI)")
    kpi_data = [["KPI Tanımı", "Birim", "Hedef", "Değerlendirici"]]
    for k in veri.get('kpi_listesi', []):
        kpi_data.append([k['kpi_adi'], k['olcum_birimi'], k['hedef_deger'], k['degerlendirici']])
    if len(kpi_data) == 1: kpi_data.append(["-","-","-","-"])
    t_k = Table(kpi_data, colWidths=[75*mm, 25*mm, 40*mm, 40*mm])
    t_k.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),('FONTSIZE',(0,0),(-1,-1),8)]))
    elements.append(t_k)
    elements.append(Spacer(1, 5*mm))

    # 10. Onay ve İmza
    _add_h("10. ONAY VE İMZA")
    imza_data = [["Hazırlayan (İK/Bölüm)", "Kontrol Eden (Kalite)", "Onaylayan (Yönetim)"], ["", "", ""]]
    t_imza = Table(imza_data, colWidths=[60*mm, 60*mm, 60*mm], rowHeights=[10*mm, 18*mm])
    t_imza.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('ALIGN',(0,0),(-1,-1),'CENTER'), ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    elements.append(t_imza)

    return True

def org_chart_pdf_uret(engine, all_depts, pers_df):
    """
    Kullanıcı talebi (ADIM 2): Kurumsal Org Şeması Üretici (ReportLab).
    landscape(A4) ve EKL-KYS-ORG-001 standartı.
    """
    buffer = BytesIO()
    doc_info = {'belge_kodu': 'EKL-KYS-ORG-001', 'belge_adi': 'ORGANİZASYON ŞEMASI', 'donem': datetime.now().strftime('%Y')}
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=35*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    d_style = ParagraphStyle('Dept', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', leftIndent=0, spaceBefore=6, spaceAfter=3)
    p_style = ParagraphStyle('Pers', parent=styles['Normal'], fontSize=9, leftIndent=10*mm)
    
    elements = []
    # En üst departmanları bul (ana_departman_id is null veya 1)
    top = all_depts[all_depts['ana_departman_id'].isna() | (all_depts['ana_departman_id'] == 1)]
    for _, d in top.iterrows():
        if d['id'] != 1:
            _render_org_recursive(elements, d['id'], d['bolum_adi'], all_depts, pers_df, d_style, p_style, 0)
    
    def my_h_f(canvas, doc):
        canvas.set_doc_info(doc_info)
        canvas.draw_header_footer()
        
    doc.build(elements, onFirstPage=my_h_f, onLaterPages=my_h_f, canvasmaker=QDMSPageNumbers)
    return buffer.getvalue()

def _render_org_recursive(elements, d_id, d_name, all_depts, pers_df, d_style, p_style, level):
    """Hiyerarşiyi ReportLab elementlerine dönüştürür (Anayasa m.5)."""
    indent = level * 8 * mm
    cur_d_style = ParagraphStyle(f'D_{d_id}', parent=d_style, leftIndent=indent)
    elements.append(Paragraph(f"🏢 {d_name}", cur_d_style))
    
    # Personel ekle
    staff = pers_df[pers_df['departman_id'] == d_id]
    for _, p in staff.iterrows():
        icon = get_position_icon(p['pozisyon_seviye'])
        p_text = f"{icon} <b>{p['ad_soyad']}</b> ({p['gorev'] or p['rol']})"
        cur_p_style = ParagraphStyle(f'P_{p["id"]}', parent=p_style, leftIndent=indent + 10*mm)
        elements.append(Paragraph(p_text, cur_p_style))
    
    # Alt departmanlar
    sub = all_depts[all_depts['ana_departman_id'] == d_id]
    for _, s in sub.iterrows():
        _render_org_recursive(elements, s['id'], s['bolum_adi'], all_depts, pers_df, d_style, p_style, level + 1)
