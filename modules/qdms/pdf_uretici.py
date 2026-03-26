"""
EKLERİSTAN QDMS — PDF Üretici Modülü
ReportLab tabanlı, BRCGS/IFS uyumlu yüksek sadakatli PDF çıktısı.
"""
import os
import pandas as pd
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _font_kaydet():
    """Windows Arial TTF fontlarını kaydet — Türkçe karakter desteği (ı, İ, ş, ğ, ö, ü, ç)."""
    font_map = {
        'Arial':        r'C:\Windows\Fonts\arial.ttf',
        'Arial-Bold':   r'C:\Windows\Fonts\arialbd.ttf',
        'Arial-Italic': r'C:\Windows\Fonts\ariali.ttf',
        'Arial-BoldI':  r'C:\Windows\Fonts\arialbi.ttf',
    }
    try:
        if os.path.exists(font_map['Arial']):
            pdfmetrics.registerFont(TTFont('Arial',       font_map['Arial']))
            pdfmetrics.registerFont(TTFont('Arial-Bold',  font_map['Arial-Bold']))
            italic = 'Arial'
            bolditalic = 'Arial-Bold'
            if os.path.exists(font_map['Arial-Italic']):
                pdfmetrics.registerFont(TTFont('Arial-Italic', font_map['Arial-Italic']))
                italic = 'Arial-Italic'
            if os.path.exists(font_map['Arial-BoldI']):
                pdfmetrics.registerFont(TTFont('Arial-BoldI', font_map['Arial-BoldI']))
                bolditalic = 'Arial-BoldI'
            # registerFontFamily → <b> ve <i> etiketleri TTF üzerinden çalışır, Helvetica'ya dönmez
            pdfmetrics.registerFontFamily(
                'Arial', normal='Arial', bold='Arial-Bold',
                italic=italic, boldItalic=bolditalic,
            )
            return 'Arial', 'Arial-Bold', italic
    except Exception:
        pass
    return 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'


FONT_N, FONT_B, FONT_I = _font_kaydet()


class QDMSPageNumbers(canvas.Canvas):
    """
    Kanuna uygun Header ve Footer çizen Canvas sınıfı.
    Sağ Blok (Ters Sıra): Baskı Tarihi (Üst) -> Rev (Orta) -> Sayfa (Alt)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._doc_info = {}
        self._saved_page_states = []

    def set_doc_info(self, info):
        self._doc_info = info

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._doc_info['total_pages'] = total
            self.draw_header_footer()
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self):
        # Ayarlar
        width, height = self._pagesize
        margin = 15 * mm
        header_y = height - 15 * mm
        
        # --- HEADER SOL: LOGO + ŞİRKET ---
        try:
            logo_data = LOGO_B64.split(",")[1]
            logo_img = BytesIO(base64.b64decode(logo_data))
            from reportlab.lib.utils import ImageReader
            self.drawImage(ImageReader(logo_img), margin, header_y - 12*mm, width=35*mm, preserveAspectRatio=True, mask='auto')
        except: pass
        
        self.setFont(FONT_B, 10)
        self.drawString(margin + 37*mm, header_y - 8*mm, "EKLERİSTAN A.Ş.")

        # --- HEADER MERKEZ: FORM ADI + KOD | DÖNEM ---
        self.setFont(FONT_B, 12)
        title = self._doc_info.get('belge_adi', 'DOKÜMAN')
        self.drawCentredString(width/2, header_y - 5*mm, title)

        self.setFont(FONT_N, 9)
        id_period = f"{self._doc_info.get('belge_kodu', '')} | {self._doc_info.get('donem', '')}"
        self.drawCentredString(width/2, header_y - 10*mm, id_period)

        # --- HEADER SAĞ (TERS SIRA KANUNU) ---
        # 1. Baskı Tarihi (En Üst)
        # 2. Rev (Orta)
        # 3. Sayfa (En Alt)
        self.setFont(FONT_N, 8)
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
        self.setFont(FONT_N, 7)
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
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, fontName=FONT_B)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8, fontName=FONT_N)
    
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
    eb_style = ParagraphStyle('EB', parent=cell_style, fontSize=8, leftIndent=5*mm, textColor=colors.grey, fontName=FONT_I)
    
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

# ── Kurumsal renk paleti (seviye bazlı) ──────────────────────────────────────
_ORG_BG  = ["#0d1f3c", "#1e4080", "#2e6da4", "#5b9bd5", "#d6e4f0", "#eef4fb"]
_ORG_FG  = ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#0d1f3c", "#0d1f3c"]
_ORG_FS  = [11,        10,        9,         8,         8,         7        ]


def _org_dept_blok(d_name, level, genislik):
    """Bölüm adı için renkli başlık kutusu (Tablo)."""
    idx   = min(level, len(_ORG_BG) - 1)
    bg    = colors.HexColor(_ORG_BG[idx])
    fg    = colors.HexColor(_ORG_FG[idx])
    fs    = _ORG_FS[idx]
    lpad  = 8 + level * 6
    stil  = ParagraphStyle(f'OH{level}', fontName=FONT_B, fontSize=fs, textColor=fg, leading=fs + 3)
    tbl   = Table([[Paragraph(d_name, stil)]], colWidths=[genislik])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), bg),
        ('LEFTPADDING',   (0, 0), (-1, -1), lpad),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return tbl


def _org_personel_tablo(staff, genislik, level):
    """Personel listesi için zebra çizgili tablo."""
    if staff.empty:
        return None
    w1, w2 = genislik * 0.45, genislik * 0.55
    lpad   = 12 + level * 6
    s_ad   = ParagraphStyle(f'OPN_{id(staff)}', fontName=FONT_B, fontSize=8, textColor=colors.HexColor("#1a1a2e"))
    s_rol  = ParagraphStyle(f'OPR_{id(staff)}', fontName=FONT_N, fontSize=7.5, textColor=colors.HexColor("#4a4a6a"))
    satirlar = []
    for _, p in staff.iterrows():
        gorev = p['gorev'] if pd.notna(p.get('gorev')) else None
        rol   = p['rol']   if pd.notna(p.get('rol'))   else None
        satirlar.append([
            Paragraph(f"• {p['ad_soyad']}", s_ad),
            Paragraph(gorev or rol or '-', s_rol),
        ])
    tbl = Table(satirlar, colWidths=[w1, w2])
    stil = [
        ('LEFTPADDING',   (0, 0), (-1, -1), lpad),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW',     (0, -1), (-1, -1), 0.3, colors.HexColor("#c8d8e8")),
    ]
    for i in range(len(satirlar)):
        bg = colors.white if i % 2 == 0 else colors.HexColor("#f0f5fb")
        stil.append(('BACKGROUND', (0, i), (-1, i), bg))
    tbl.setStyle(TableStyle(stil))
    return tbl


def _render_org_blok(elements, d_id, d_name, all_depts, pers_df, level, genislik):
    """Bölüm + personel bloğunu elements'e ekler (Anayasa m.5 — maks 30 satır)."""
    from reportlab.platypus import CondPageBreak
    elements.append(CondPageBreak(22 * mm))
    elements.append(_org_dept_blok(d_name, level, genislik))
    staff    = pers_df[pers_df['departman_id'] == d_id]
    pers_tbl = _org_personel_tablo(staff, genislik, level)
    if pers_tbl:
        elements.append(pers_tbl)
    elements.append(Spacer(1, 1.5 * mm))
    sub = all_depts[all_depts['ana_departman_id'] == d_id]
    for _, s in sub.iterrows():
        _render_org_blok(elements, s['id'], s['bolum_adi'], all_depts, pers_df, level + 1, genislik)


def org_chart_pdf_uret(engine, all_depts, pers_df):
    """Kurumsal Org Şeması — landscape A4, EKL-KYS-ORG-001, kurumsal renk paleti."""
    buffer   = BytesIO()
    doc_info = {
        'belge_kodu': 'EKL-KYS-ORG-001',
        'belge_adi':  'ORGANİZASYON ŞEMASI',
        'donem':      datetime.now().strftime('%Y'),
    }
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        topMargin=38 * mm, bottomMargin=22 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
    )
    genislik = landscape(A4)[0] - 30 * mm

    all_depts['id']              = pd.to_numeric(all_depts['id'],              errors='coerce')
    all_depts['ana_departman_id'] = pd.to_numeric(all_depts['ana_departman_id'], errors='coerce')
    pers_df['departman_id']      = pd.to_numeric(pers_df['departman_id'],      errors='coerce')

    elements = []
    top = all_depts[all_depts['ana_departman_id'].isna()]
    for _, d in top.iterrows():
        _render_org_blok(elements, d['id'], d['bolum_adi'], all_depts, pers_df, 0, genislik)

    def my_h_f(c, doc):
        c.set_doc_info(doc_info)
        c.draw_header_footer()

    doc.build(elements, onFirstPage=my_h_f, onLaterPages=my_h_f, canvasmaker=QDMSPageNumbers)
    return buffer.getvalue()
