"""
EKLERİSTAN QMS — Bağlantı & Fonksiyon Haritası PDF Üretici
Kaynak: .antigravity/musbet/hafiza/sistem_baglanti_haritasi.md
Çıktı : docs/EKLERISTAN_QMS_BAGLANTI_HARITASI.pdf
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, CondPageBreak, HRFlowable,
    KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ─── Font Kayıt ──────────────────────────────────────────────────────────────

FONT_NAME = "Helvetica"

def _font_kaydet():
    global FONT_NAME
    font_paths = [
        ("C:/Windows/Fonts/arial.ttf",    "C:/Windows/Fonts/arialbd.ttf",   "Arial"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVu"),
    ]
    for reg, bold, name in font_paths:
        if os.path.exists(reg) and os.path.exists(bold):
            try:
                pdfmetrics.registerFont(TTFont(name, reg))
                pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold))
                pdfmetrics.registerFontFamily(name, normal=name, bold=f"{name}-Bold")
                FONT_NAME = name
                return
            except Exception:
                pass

_font_kaydet()

# ─── Renkler ─────────────────────────────────────────────────────────────────

C_NAVY    = colors.HexColor("#0d1f3c")
C_BLUE    = colors.HexColor("#1e4080")
C_ORANGE  = colors.HexColor("#e67e22")
C_LGRAY   = colors.HexColor("#f5f5f5")
C_MGRAY   = colors.HexColor("#cccccc")
C_CODE_BG = colors.HexColor("#1e1e2e")
C_CODE_FG = colors.HexColor("#cdd6f4")
C_TH_BG   = colors.HexColor("#2d4a7a")
C_TH_FG   = colors.white

# ─── Stiller ─────────────────────────────────────────────────────────────────

S = {}

def _stiller_olustur():
    global S
    F = FONT_NAME
    FB = f"{F}-Bold" if F != "Helvetica" else "Helvetica-Bold"
    S = {
        "cover_title": ParagraphStyle("cover_title", fontName=FB, fontSize=28,
                                       textColor=colors.white, alignment=1, spaceAfter=4),
        "cover_sub":   ParagraphStyle("cover_sub",   fontName=F,  fontSize=14,
                                       textColor=colors.white, alignment=1),
        "h1":  ParagraphStyle("h1", fontName=FB, fontSize=16, textColor=C_NAVY,
                               spaceBefore=10, spaceAfter=4, borderPad=2),
        "h2":  ParagraphStyle("h2", fontName=FB, fontSize=13, textColor=C_BLUE,
                               spaceBefore=8, spaceAfter=3),
        "h3":  ParagraphStyle("h3", fontName=FB, fontSize=11, textColor=C_ORANGE,
                               spaceBefore=6, spaceAfter=2),
        "h4":  ParagraphStyle("h4", fontName=FB, fontSize=10, textColor=C_BLUE,
                               spaceBefore=4, spaceAfter=1),
        "body": ParagraphStyle("body", fontName=F, fontSize=9, leading=13,
                                spaceAfter=3),
        "bullet": ParagraphStyle("bullet", fontName=F, fontSize=9, leading=12,
                                  leftIndent=10, bulletIndent=0, spaceAfter=2),
        "bq":  ParagraphStyle("bq", fontName=F, fontSize=9, leading=12,
                               leftIndent=8, textColor=colors.HexColor("#555555"),
                               borderPad=4),
        "th":  ParagraphStyle("th", fontName=FB, fontSize=8, textColor=C_TH_FG,
                               alignment=1),
        "td":  ParagraphStyle("td", fontName=F,  fontSize=8, leading=11),
        "code": ParagraphStyle("code", fontName="Courier", fontSize=8, leading=11,
                                textColor=C_CODE_FG),
        "toc_title": ParagraphStyle("toc_title", fontName=FB, fontSize=14,
                                     textColor=C_NAVY, spaceAfter=6),
        "toc_h1": ParagraphStyle("toc_h1", fontName=FB, fontSize=9, textColor=C_NAVY,
                                  spaceBefore=4),
        "toc_h2": ParagraphStyle("toc_h2", fontName=F, fontSize=8, textColor=C_BLUE,
                                  leftIndent=8),
        "caption": ParagraphStyle("caption", fontName=F, fontSize=8,
                                   textColor=colors.HexColor("#666666"), alignment=1),
    }

_stiller_olustur()

# ─── Canvas (Header/Footer) ──────────────────────────────────────────────────

class BaglantCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def _draw_header_footer(self, page_count):
        w, h = A4
        page_num = self._pageNumber
        if page_num <= 1:
            return
        # Header çizgisi
        self.setStrokeColor(C_BLUE)
        self.setLineWidth(0.5)
        self.line(14*mm, h - 14*mm, w - 14*mm, h - 14*mm)
        self.setFont(FONT_NAME if FONT_NAME != "Helvetica" else "Helvetica", 7)
        self.setFillColor(C_BLUE)
        self.drawString(14*mm, h - 12*mm, "EKLERİSTAN QMS — Bağlantı & Fonksiyon Haritası")
        self.drawRightString(w - 14*mm, h - 12*mm, f"v1.0 | {datetime.now().strftime('%d.%m.%Y')}")
        # Footer
        self.setStrokeColor(C_MGRAY)
        self.line(14*mm, 14*mm, w - 14*mm, 14*mm)
        self.setFillColor(colors.HexColor("#888888"))
        self.drawString(14*mm, 10*mm, "GİZLİ — Sadece yetkili personele açıktır.")
        self.drawRightString(w - 14*mm, 10*mm, f"Sayfa {page_num} / {page_count}")

# ─── Yardımcı Fonksiyonlar ───────────────────────────────────────────────────

import re
import xml.sax.saxutils as saxutils

def _escape(t: str) -> str:
    t = saxutils.escape(str(t))
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`',       r'<font face="Courier">\1</font>', t)
    return t

def _parse_md_table(lines):
    rows = []
    for line in lines:
        line = line.strip()
        if not line or set(line.replace(' ', '').replace('|', '').replace('-', '').replace(':', '')) == set():
            continue
        if re.match(r'^\|?[-:| ]+\|?$', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cells)
    return rows

def _md_table_to_rl(rows):
    if not rows:
        return None
    max_cols = max(len(r) for r in rows)
    norm = [r + [''] * (max_cols - len(r)) for r in rows]
    rl_rows = []
    for ri, row in enumerate(norm):
        rl_row = []
        style = S['th'] if ri == 0 else S['td']
        for cell in row:
            rl_row.append(Paragraph(_escape(cell), style))
        rl_rows.append(rl_row)

    col_w = (181 * mm) / max_cols
    t = Table(rl_rows, colWidths=[col_w] * max_cols, repeatRows=1)
    ts = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_TH_BG),
        ('GRID',       (0, 0), (-1, -1), 0.3, C_MGRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_LGRAY]),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ])
    t.setStyle(ts)
    return t

def _render_code_block(lines):
    parts = []
    for line in lines:
        safe = saxutils.escape(line).replace(' ', '&nbsp;')
        parts.append(f'<font face="Courier" color="#cdd6f4">{safe}</font>')
    inner = '<br/>'.join(parts)
    p = Paragraph(inner, S['code'])
    data = [[p]]
    t = Table(data, colWidths=[181*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_CODE_BG),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    return t

def _md_to_elements(md_text: str) -> list:
    elems = []
    lines = md_text.splitlines()
    i = 0
    in_code = False
    code_lines = []
    table_lines = []
    in_table = False

    while i < len(lines):
        line = lines[i]

        # Kod bloğu başlangıç/bitiş
        if line.strip().startswith('```'):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                if code_lines:
                    elems.append(_render_code_block(code_lines))
                    elems.append(Spacer(1, 3*mm))
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # Tablo
        if line.strip().startswith('|'):
            table_lines.append(line)
            i += 1
            continue
        else:
            if table_lines:
                rows = _parse_md_table(table_lines)
                tbl = _md_table_to_rl(rows)
                if tbl:
                    elems.append(tbl)
                    elems.append(Spacer(1, 3*mm))
                table_lines = []

        stripped = line.strip()

        # Boş satır
        if not stripped:
            elems.append(Spacer(1, 2*mm))
            i += 1
            continue

        # Yatay çizgi
        if re.match(r'^---+$', stripped):
            elems.append(HRFlowable(width="100%", thickness=0.5, color=C_MGRAY, spaceAfter=3))
            i += 1
            continue

        # Başlıklar
        if stripped.startswith('#### '):
            elems.append(Paragraph(_escape(stripped[5:]), S['h4']))
        elif stripped.startswith('### '):
            elems.append(Paragraph(_escape(stripped[4:]), S['h3']))
        elif stripped.startswith('## '):
            elems.append(CondPageBreak(60*mm))
            elems.append(Paragraph(_escape(stripped[3:]), S['h2']))
        elif stripped.startswith('# '):
            elems.append(PageBreak())
            elems.append(Paragraph(_escape(stripped[2:]), S['h1']))

        # Blockquote
        elif stripped.startswith('> '):
            text = stripped[2:]
            data = [[Paragraph(_escape(text), S['bq'])]]
            t = Table(data, colWidths=[181*mm])
            t.setStyle(TableStyle([
                ('LEFTPADDING',   (0, 0), (-1, -1), 10),
                ('TOPPADDING',    (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LINEBEFORE',    (0, 0), (0, -1), 3, C_ORANGE),
                ('BACKGROUND',    (0, 0), (-1, -1), C_LGRAY),
            ]))
            elems.append(t)

        # Liste öğesi
        elif stripped.startswith('- ') or stripped.startswith('* '):
            text = stripped[2:]
            indent = (len(line) - len(line.lstrip())) // 2
            style = ParagraphStyle(
                f"bullet_{indent}", parent=S['bullet'],
                leftIndent=10 + indent * 8, bulletIndent=4 + indent * 8
            )
            elems.append(Paragraph(f"• {_escape(text)}", style))

        # Numaralı liste
        elif re.match(r'^\d+\.\s', stripped):
            text = re.sub(r'^\d+\.\s', '', stripped)
            elems.append(Paragraph(_escape(text), S['bullet']))

        # Normal metin
        else:
            elems.append(Paragraph(_escape(stripped), S['body']))

        i += 1

    # Tabloda takılı kaldıysa
    if table_lines:
        rows = _parse_md_table(table_lines)
        tbl = _md_table_to_rl(rows)
        if tbl:
            elems.append(tbl)

    return elems


# ─── Kapak Sayfası ───────────────────────────────────────────────────────────

def _kapak_sayfasi() -> list:
    elems = []
    elems.append(Spacer(1, 30*mm))

    header_data = [[Paragraph("EKLERİSTAN QMS", S['cover_title'])]]
    sub_data    = [[Paragraph("Tam Bağlantı, Fonksiyon &amp; Veritabanı Haritası", S['cover_sub'])]]
    for d in [header_data, sub_data]:
        t = Table(d, colWidths=[181*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), C_NAVY),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elems.append(t)

    elems.append(Spacer(1, 8*mm))

    meta = [
        ["Versiyon", "1.0 — Kaynak Koddan Birebir"],
        ["Tarih",    datetime.now().strftime("%d.%m.%Y")],
        ["Kapsam",   "Her Dosya · Her Fonksiyon · Her Tablo · Her Bağımlılık"],
        ["Kaynak",   ".antigravity/musbet/hafiza/sistem_baglanti_haritasi.md"],
        ["Durum",    "Onaylı — Emre Bey"],
    ]
    meta_data = [[Paragraph(f"<b>{_escape(k)}</b>", S['td']),
                  Paragraph(_escape(v), S['td'])] for k, v in meta]
    mt = Table(meta_data, colWidths=[40*mm, 141*mm])
    mt.setStyle(TableStyle([
        ('GRID',          (0, 0), (-1, -1), 0.4, C_MGRAY),
        ('ROWBACKGROUNDS',(0, 0), (-1, -1), [colors.white, C_LGRAY]),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
    ]))
    elems.append(mt)
    elems.append(Spacer(1, 12*mm))
    elems.append(Paragraph(
        "Bu döküman EKLERİSTAN QMS sisteminin tüm modül-dosya bağımlılıklarını, "
        "veritabanı tablolarını, logic fonksiyonlarını, yetki akışını ve önbellek "
        "katmanlarını insan tarafından okunabilir biçimde açıklamaktadır.",
        S['body']
    ))
    elems.append(PageBreak())
    return elems


# ─── İçindekiler ─────────────────────────────────────────────────────────────

def _toc_sayfasi(md_text: str) -> list:
    elems = []
    elems.append(Paragraph("İÇİNDEKİLER", S['toc_title']))
    elems.append(HRFlowable(width="100%", thickness=1, color=C_BLUE, spaceAfter=4))

    headings = []
    for line in md_text.splitlines():
        s = line.strip()
        if s.startswith('## '):
            headings.append((2, s[3:]))
        elif s.startswith('### '):
            headings.append((3, s[4:]))

    toc_rows = []
    for level, title in headings:
        style = S['toc_h1'] if level == 2 else S['toc_h2']
        toc_rows.append([Paragraph(_escape(title), style), Paragraph("", style)])

    if toc_rows:
        toc_table = Table(toc_rows, colWidths=[160*mm, 21*mm])
        toc_table.setStyle(TableStyle([
            ('GRID',           (0, 0), (-1, -1), 0,  colors.white),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, C_LGRAY]),
            ('TOPPADDING',     (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 3),
            ('LEFTPADDING',    (0, 0), (-1, -1), 4),
        ]))
        elems.append(toc_table)
    return elems


# ─── Son Sayfa ────────────────────────────────────────────────────────────────

def _son_sayfa() -> list:
    elems = [Spacer(1, 40*mm)]
    footer_data = [[Paragraph(
        "<b>EKLERİSTAN QMS — Tam Bağlantı &amp; Fonksiyon Haritası</b><br/>"
        f"Versiyon 1.0 | Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')}<br/>"
        "Bu döküman .antigravity/musbet/hafiza/sistem_baglanti_haritasi.md "
        "kaynak dosyasından otomatik olarak üretilmiştir.",
        S['caption']
    )]]
    ft = Table(footer_data, colWidths=[181*mm])
    ft.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_LGRAY),
        ('BOX',           (0, 0), (-1, -1), 0.5, C_MGRAY),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGNMENT',     (0, 0), (-1, -1), 'CENTER'),
    ]))
    elems.append(ft)
    return elems


# ─── Ana Fonksiyon ────────────────────────────────────────────────────────────

def pdf_uret(md_path: str, output_path: str):
    print(f"[INFO] Kaynak : {md_path}")
    print(f"[INFO] Çıktı  : {output_path}")

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=portrait(A4),
        topMargin=18*mm, bottomMargin=18*mm,
        leftMargin=14*mm, rightMargin=14*mm,
        title="EKLERİSTAN QMS — Tam Bağlantı, Fonksiyon & Veritabanı Haritası",
        author="EKLERİSTAN QMS",
        subject="Sistem Bağlantı Haritası v1.0",
    )

    elements = []
    elements.extend(_kapak_sayfasi())
    elements.extend(_toc_sayfasi(md_text))
    elements.append(PageBreak())
    elements.extend(_md_to_elements(md_text))
    elements.append(PageBreak())
    elements.extend(_son_sayfa())

    doc.build(elements, canvasmaker=BaglantCanvas)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"[OK] PDF oluşturuldu: {output_path}  ({size_kb} KB)")
    return output_path


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    MD   = os.path.join(BASE, '.antigravity', 'musbet', 'hafiza', 'sistem_baglanti_haritasi.md')
    OUT  = os.path.join(BASE, 'docs', 'EKLERISTAN_QMS_BAGLANTI_HARITASI.pdf')

    if not os.path.exists(MD):
        print(f"[HATA] Kaynak bulunamadı: {MD}")
        sys.exit(1)

    pdf_uret(MD, OUT)
    import subprocess
    subprocess.Popen(['cmd', '/c', 'start', '', OUT])
    print("[INFO] PDF görüntüleyici açılıyor...")
