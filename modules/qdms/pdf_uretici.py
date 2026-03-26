"""
EKLERİSTAN QDMS — PDF Üretici Modülü
ReportLab tabanlı, BRCGS/IFS uyumlu yüksek sadakatli PDF çıktısı.
"""
import os
import tempfile
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

# Logoyu geçici PNG dosyasına çıkar — canvas.drawImage() dosya yoluyla güvenilir çalışır
def _logo_path_hazirla() -> str:
    # v4.0.3: Logo dosyasını her seferinde kontrol et/oluştur
    try:
        logo_data = LOGO_B64.split(",")[1]
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(base64.b64decode(logo_data))
            return tmp.name
    except Exception as e:
        print(f"PDF_LOG_ERROR: Logo file creation failed: {e}")
        return ""

_LOGO_PATH = _logo_path_hazirla()


def _font_kaydet():
    """
    PDF fontlarını kaydet — Türkçe Extended-A desteği (İ ı Ş Ğ Ü Ç Ö).
    Öncelik: Vera (ReportLab built-in, garantili) → Arial → Helvetica fallback.
    Arial ReportLab CID encoding'iyle Latin Extended-A'yı doğru gösteremiyor.
    """
    import reportlab as _rl
    rl_fonts = os.path.join(os.path.dirname(_rl.__file__), 'fonts')
    candidates = [
        {
            'family':   'Vera',
            'normal':   os.path.join(rl_fonts, 'Vera.ttf'),
            'bold':     os.path.join(rl_fonts, 'VeraBd.ttf'),
            'italic':   os.path.join(rl_fonts, 'VeraIt.ttf'),
            'boldital': os.path.join(rl_fonts, 'VeraBI.ttf'),
        },
        {
            'family':   'Arial',
            'normal':   r'C:\Windows\Fonts\arial.ttf',
            'bold':     r'C:\Windows\Fonts\arialbd.ttf',
            'italic':   r'C:\Windows\Fonts\ariali.ttf',
            'boldital': r'C:\Windows\Fonts\arialbi.ttf',
        },
    ]
    for c in candidates:
        if not (os.path.exists(c['normal']) and os.path.exists(c['bold'])):
            continue
        try:
            fam = c['family']
            pdfmetrics.registerFont(TTFont(fam,          c['normal']))
            pdfmetrics.registerFont(TTFont(f'{fam}-Bold', c['bold']))
            ita = fam
            bia = f'{fam}-Bold'
            if os.path.exists(c['italic']):
                pdfmetrics.registerFont(TTFont(f'{fam}-Italic', c['italic']))
                ita = f'{fam}-Italic'
            if os.path.exists(c['boldital']):
                pdfmetrics.registerFont(TTFont(f'{fam}-BoldI', c['boldital']))
                bia = f'{fam}-BoldI'
            pdfmetrics.registerFontFamily(fam, normal=fam, bold=f'{fam}-Bold',
                                          italic=ita, boldItalic=bia)
            return fam, f'{fam}-Bold', ita
        except Exception:
            continue
    return 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'


FONT_N, FONT_B, FONT_I = _font_kaydet()


class EKLCanvas(canvas.Canvas):
    """
    Tek-pas canvas — logo dahil tam header/footer çizer.
    Sayfa X/Y için çift-build tekniği kullanılır (iki-pas state yok).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._qdms_info = {}
        self._qdms_total = 1

    def set_doc_info(self, info, total_pages=1):
        self._qdms_info = info
        self._qdms_total = total_pages

    def draw_header_footer(self, current_page):
        """Sadeleştirilmiş Kurumsal Header/Footer."""
        width, height = self._pagesize
        margin   = 15 * mm
        header_y = height - 15 * mm
        footer_y = 12 * mm

        # --- LOGO (sol üst) ---
        global _LOGO_PATH
        if not _LOGO_PATH or not os.path.exists(_LOGO_PATH):
            _LOGO_PATH = _logo_path_hazirla()

        if _LOGO_PATH and os.path.exists(_LOGO_PATH):
            try:
                self.drawImage(_LOGO_PATH, margin, header_y - 12 * mm,
                               width=35 * mm, preserveAspectRatio=True, mask=None)
            except Exception as e:
                print(f"PDF_LOG_ERROR: drawImage failed: {e}")

        # --- SAĞ ÜST (Revizyon Bilgileri) ---
        self.setFont(FONT_N, 8)
        self.drawRightString(width - margin, header_y,
                               f"Rev No: {self._qdms_info.get('rev_no','01')}")
        self.drawRightString(width - margin, header_y - 4 * mm,
                               f"Rev Tarihi: {self._qdms_info.get('rev_tarihi','')}")

        # --- BAŞLIK (merkez) ---
        self.setFont(FONT_B, 11)
        self.drawCentredString(width / 2, header_y - 5 * mm,
                               self._qdms_info.get('belge_adi', 'DOKÜMAN').upper())
        self.setFont(FONT_N, 8)
        self.drawCentredString(
            width / 2, header_y - 10 * mm,
            f"{self._qdms_info.get('belge_kodu','')} | İlk Yayın: {self._qdms_info.get('ilk_yayin_tarihi', '')}"
        )

        # --- SEPARATOR ---
        self.setStrokeColor(colors.HexColor("#0d1f3c"))
        self.setLineWidth(0.5)
        self.line(margin, header_y - 15 * mm, width - margin, header_y - 15 * mm)

        # --- FOOTER ---
        self.setFont(FONT_N, 7)
        # Sol Alt: Sadece Dahili Kullanım
        self.drawString(margin, footer_y, "DAHİLİ KULLANIM")
        
        # Merkez Alt: Sadeleştirilmiş Versiyon
        self.drawCentredString(width / 2, footer_y, "EKLERİSTAN QMS v3.2")
        
        # Sağ Alt: Baskı Tarihi + Sayfa No
        baski_metni = (f"BASKI TARİHİ: {datetime.now().strftime('%d.%m.%Y %H:%M')} | "
                       f"SAYFA: {current_page} / {self._qdms_total}")
        self.drawRightString(width - margin, footer_y, baski_metni)


# Geriye dönük uyumluluk için alias
QDMSPageNumbers = EKLCanvas


def _sayfa_say(elements_kopy, orient):
    """Sayfa sayısını ölç (logo çizmeden hızlı pas)."""
    sayac = [0]

    class _SayacCanvas(canvas.Canvas):
        def showPage(self):
            sayac[0] += 1
            super().showPage()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=orient, topMargin=35*mm, bottomMargin=20*mm)
    try:
        doc.build(elements_kopy)
    except Exception:
        pass
    return max(sayac[0], 1)

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
        'rev_tarihi': veri.get('rev_tarihi', datetime.now().strftime('%d.%m.%Y')),
        'durum': veri.get('durum', 'AKTİF'),
        'ilk_yayin_tarihi': veri.get('ilk_yayin_tarihi', datetime.now().strftime('%d.%m.%Y'))
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

    # 6. İMZA BLOĞU (BRC/IFS zorunlu: hazırlayan, kontrol, onay)
    elements += _imza_blogu_olustur(veri, header_style, cell_style)

    # Pas 1: Sayfa sayısını öğren (logo yok, sadece layout)
    import copy
    total_sayfa = _sayfa_say(copy.deepcopy(elements), orient)

    # Pas 2: Gerçek build — EKLCanvas, logo + doğru X/Y
    def my_header_footer(c, doc):
        c.set_doc_info(doc_info, total_sayfa)
        c.draw_header_footer(doc.page)

    doc.build(elements, onFirstPage=my_header_footer, onLaterPages=my_header_footer,
              canvasmaker=EKLCanvas)
    
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


def _imza_blogu_olustur(veri, header_style, cell_style):
    """Hazırlayan / Kontrol Eden / Onaylayan imza tablosu. BRC v9 3.7, IFS v8 4.2.1"""
    varsayilan = [
        {'rol': 'Hazırlayan', 'ad_soyad': '', 'gorev': ''},
        {'rol': 'Kontrol Eden', 'ad_soyad': '', 'gorev': ''},
        {'rol': 'Onaylayan', 'ad_soyad': '', 'gorev': ''},
    ]
    imzalar = veri.get('imzalar', varsayilan)
    nav_stil = ParagraphStyle('ImzaNav', parent=header_style, fontSize=8,
                              textColor=colors.white, alignment=1)
    icerik_stil = ParagraphStyle('ImzaIcerik', parent=cell_style, fontSize=8, alignment=1)

    baslik_satiri = [Paragraph(f"<b>{i['rol'].upper()}</b>", nav_stil) for i in imzalar]
    ad_satiri    = [Paragraph(i.get('ad_soyad') or '_________________________', icerik_stil)
                   for i in imzalar]
    gorev_satiri = [Paragraph(i.get('gorev') or '_________________________', icerik_stil)
                   for i in imzalar]
    imza_satiri  = [Paragraph("İmza: ________________________", icerik_stil) for _ in imzalar]
    # v4.0.3: Dinamik onay tarihleri
    tarih_satiri = [Paragraph(f"Tarih: {i.get('tarih') or '_____ / _____ / _______'}", icerik_stil) 
                    for i in imzalar]

    col_w = [59*mm, 59*mm, 59*mm]
    tbl = Table([baslik_satiri, ad_satiri, gorev_satiri, imza_satiri, tarih_satiri],
                colWidths=col_w)
    tbl.setStyle(TableStyle([
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#0d1f3c')),
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#0d1f3c')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWHEIGHT',     (0, 1), (-1, -1), 18),
    ]))
    label_stil = ParagraphStyle('ImzaLabel', parent=header_style, fontSize=9,
                                textColor=colors.HexColor('#0d1f3c'))
    return [Spacer(1, 12*mm),
            tbl]


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


def _add_kurumsal_kimlik_pdf(elements, all_depts, pers_df, genislik):
    """PDF için üst metrik kartları ekler (BRC v9 1.1.2 uyumlu)."""
    toplam = len(pers_df)
    styles = getSampleStyleSheet()
    s_label = ParagraphStyle('SKL', fontName=FONT_B, fontSize=8, textColor=colors.HexColor("#4a4a6a"), alignment=1)
    s_val   = ParagraphStyle('SKV', fontName=FONT_B, fontSize=12, textColor=colors.HexColor("#0d1f3c"), alignment=1)
    s_perc  = ParagraphStyle('SKP', fontName=FONT_I, fontSize=7, textColor=colors.HexColor("#2e7d32"), alignment=1)

    ana_bolumler = all_depts[all_depts['ana_departman_id'].isna() | (all_depts['ana_departman_id'] == 1)]
    ana_bolumler = ana_bolumler[ana_bolumler['id'] != 1]
    
    # 4'lü gruplar halinde kartları oluştur
    for i in range(0, len(ana_bolumler), 4):
        chunk = ana_bolumler.iloc[i:i+4]
        row_cells = []
        for _, bolum in chunk.iterrows():
            from logic.data_fetcher import get_all_sub_department_ids
            alt_ids = get_all_sub_department_ids(bolum['id'])
            sayi = int(pers_df[pers_df['departman_id'].isin(alt_ids)].shape[0])
            oran = f"%{round(sayi / toplam * 100, 1)}" if toplam > 0 else "%0"
            
            cell_content = [
                Paragraph(bolum['bolum_adi'].upper(), s_label),
                Spacer(1, 1*mm),
                Paragraph(str(sayi), s_val),
                Paragraph(oran, s_perc)
            ]
            row_cells.append(cell_content)
        
        # Boş hücreleri tamamla
        while len(row_cells) < 4: row_cells.append("")
        
        t = Table([row_cells], colWidths=[genislik/4]*4)
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d9e6")),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f4f7f9")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4*mm))

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
    
    # 0. Kurumsal Kimlik Bloğu
    _add_kurumsal_kimlik_pdf(elements, all_depts, pers_df, genislik)
    elements.append(Spacer(1, 5*mm))

    top = all_depts[all_depts['ana_departman_id'].isna() | (all_depts['ana_departman_id'] == 1)]
    top = top[top['id'] != 1]
    
    for _, d in top.iterrows():
        _render_org_blok(elements, d['id'], d['bolum_adi'], all_depts, pers_df, 0, genislik)

    def my_h_f(c, doc):
        c.set_doc_info(doc_info)
        # BUG FIX: draw_header_footer requires current_page argument
        c.draw_header_footer(doc.page)

    doc.build(elements, onFirstPage=my_h_f, onLaterPages=my_h_f, canvasmaker=QDMSPageNumbers)
    return buffer.getvalue()
