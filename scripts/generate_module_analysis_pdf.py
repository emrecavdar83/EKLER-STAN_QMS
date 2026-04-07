"""
EKLERİSTAN QMS — Sistem & Modül Derin Analiz PDF Üretici
Versiyon: 2.0 (v6.0 markdown ile tam uyumlu)

Çalıştırmak için (proje kökünden):
    python scripts/generate_module_analysis_pdf.py
"""

import os
import sys
import re
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

def _font_kaydet():
    """Türkçe karakter destekli font — Arial → Vera → Helvetica zinciri."""
    import reportlab as _rl
    rl_fonts = os.path.join(os.path.dirname(_rl.__file__), 'fonts')
    candidates = [
        {
            'family': 'Arial',
            'normal': r'C:\Windows\Fonts\arial.ttf',
            'bold':   r'C:\Windows\Fonts\arialbd.ttf',
            'italic': r'C:\Windows\Fonts\ariali.ttf',
        },
        {
            'family': 'Vera',
            'normal': os.path.join(rl_fonts, 'Vera.ttf'),
            'bold':   os.path.join(rl_fonts, 'VeraBd.ttf'),
            'italic': os.path.join(rl_fonts, 'VeraIt.ttf'),
        },
    ]
    for c in candidates:
        if not (os.path.exists(c['normal']) and os.path.exists(c['bold'])):
            continue
        try:
            fam = c['family']
            pdfmetrics.registerFont(TTFont(fam, c['normal']))
            pdfmetrics.registerFont(TTFont(f'{fam}-Bold', c['bold']))
            ita = fam
            if os.path.exists(c.get('italic', '')):
                pdfmetrics.registerFont(TTFont(f'{fam}-Italic', c['italic']))
                ita = f'{fam}-Italic'
            pdfmetrics.registerFontFamily(
                fam, normal=fam, bold=f'{fam}-Bold', italic=ita, boldItalic=f'{fam}-Bold'
            )
            return fam, f'{fam}-Bold', ita
        except Exception:
            continue
    return 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'


FN, FB, FI = _font_kaydet()

# ─── Renk Paleti ─────────────────────────────────────────────────────────────

C_NAVY    = colors.HexColor("#0d1f3c")
C_BLUE    = colors.HexColor("#1e4080")
C_LBLUE   = colors.HexColor("#2e6db4")
C_ACCENT  = colors.HexColor("#3498db")
C_ORANGE  = colors.HexColor("#e67e22")
C_GREEN   = colors.HexColor("#27ae60")
C_RED     = colors.HexColor("#e74c3c")
C_YELLOW  = colors.HexColor("#f39c12")
C_LGRAY   = colors.HexColor("#f4f6f9")
C_MGRAY   = colors.HexColor("#dde3ed")
C_DGRAY   = colors.HexColor("#555555")
C_CODE_BG = colors.HexColor("#1e1e2e")
C_CODE_FG = colors.HexColor("#cdd6f4")
C_WARN_BG = colors.HexColor("#fff3cd")
C_INFO_BG = colors.HexColor("#e8f4fd")

# ─── Stil Tanımları ───────────────────────────────────────────────────────────

def _stiller():
    cover_title = ParagraphStyle(
        'CoverTitle', fontName=FB, fontSize=22, textColor=colors.white,
        alignment=1, spaceAfter=6, leading=28
    )
    cover_sub = ParagraphStyle(
        'CoverSub', fontName=FN, fontSize=11, textColor=colors.HexColor("#b0c4de"),
        alignment=1, spaceAfter=4
    )
    toc_item = ParagraphStyle(
        'TocItem', fontName=FN, fontSize=9, textColor=C_NAVY,
        leftIndent=4*mm, spaceAfter=2
    )
    h1 = ParagraphStyle(
        'H1', fontName=FB, fontSize=14, textColor=colors.white,
        spaceBefore=4, spaceAfter=4, leading=18,
        backColor=C_NAVY, borderPad=(4, 4, 4, 8)
    )
    h2 = ParagraphStyle(
        'H2', fontName=FB, fontSize=11, textColor=C_NAVY,
        spaceBefore=8, spaceAfter=3, leading=14,
        leftIndent=0, borderWidth=0,
        borderPad=(2, 2, 2, 4)
    )
    h3 = ParagraphStyle(
        'H3', fontName=FB, fontSize=10, textColor=C_BLUE,
        spaceBefore=5, spaceAfter=2, leading=13,
        leftIndent=3*mm
    )
    h4 = ParagraphStyle(
        'H4', fontName=FB, fontSize=9, textColor=C_LBLUE,
        spaceBefore=4, spaceAfter=2, leading=12,
        leftIndent=6*mm
    )
    body = ParagraphStyle(
        'Body', fontName=FN, fontSize=8.5, textColor=colors.black,
        leading=12, spaceAfter=2, leftIndent=3*mm
    )
    bullet = ParagraphStyle(
        'Bullet', fontName=FN, fontSize=8.5, textColor=colors.black,
        leading=11, spaceAfter=1, leftIndent=8*mm, firstLineIndent=-4*mm
    )
    blockquote = ParagraphStyle(
        'BQ', fontName=FI, fontSize=8, textColor=C_DGRAY,
        leading=11, spaceAfter=2, leftIndent=8*mm,
        backColor=C_INFO_BG, borderPad=(3, 3, 3, 6)
    )
    code = ParagraphStyle(
        'Code', fontName='Courier', fontSize=7, textColor=C_CODE_FG,
        leading=9.5, spaceAfter=0, leftIndent=0,
        backColor=C_CODE_BG, borderPad=(4, 4, 4, 4)
    )
    th = ParagraphStyle(
        'TH', fontName=FB, fontSize=8, textColor=colors.white,
        alignment=1, leading=10
    )
    td = ParagraphStyle(
        'TD', fontName=FN, fontSize=8, textColor=colors.black,
        leading=10, spaceAfter=0
    )
    td_code = ParagraphStyle(
        'TDCode', fontName='Courier', fontSize=7, textColor=C_NAVY,
        leading=9, spaceAfter=0
    )
    caption = ParagraphStyle(
        'Caption', fontName=FI, fontSize=7.5, textColor=C_DGRAY,
        leading=10, spaceAfter=1, leftIndent=3*mm
    )
    warn = ParagraphStyle(
        'Warn', fontName=FB, fontSize=8.5, textColor=C_NAVY,
        leading=12, spaceAfter=2, leftIndent=6*mm,
        backColor=C_WARN_BG, borderPad=(3, 3, 3, 6)
    )
    return dict(
        cover_title=cover_title, cover_sub=cover_sub, toc_item=toc_item,
        h1=h1, h2=h2, h3=h3, h4=h4,
        body=body, bullet=bullet, blockquote=blockquote,
        code=code, th=th, td=td, td_code=td_code, caption=caption, warn=warn
    )


S = _stiller()

# ─── Canvas: Header / Footer ─────────────────────────────────────────────────

class AnalysisCanvas(canvas.Canvas):
    """Her sayfaya kurumsal header + footer basar."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._page_count = 0

    def showPage(self):
        self._page_count += 1
        self._draw_chrome()
        super().showPage()

    def save(self):
        self._draw_chrome()
        super().save()

    def _draw_chrome(self):
        w, h = self._pagesize
        pg = self._pageNumber

        # ── Üst çizgi ──
        self.setStrokeColor(C_NAVY)
        self.setLineWidth(1.5)
        self.line(12*mm, h - 12*mm, w - 12*mm, h - 12*mm)

        # ── Başlık metni ──
        self.setFont(FB, 7.5)
        self.setFillColor(C_NAVY)
        self.drawString(12*mm, h - 10*mm, "EKLERİSTAN QMS")
        self.setFont(FN, 7)
        self.setFillColor(C_DGRAY)
        self.drawRightString(w - 12*mm, h - 10*mm,
                             "Sistem & Modül Derin Analiz Rehberi — v6.0")

        # ── Alt çizgi ──
        self.setStrokeColor(C_NAVY)
        self.setLineWidth(0.8)
        self.line(12*mm, 10*mm, w - 12*mm, 10*mm)

        # ── Sayfa numarası ──
        self.setFont(FN, 7)
        self.setFillColor(C_DGRAY)
        self.drawCentredString(w / 2, 6.5*mm, f"Sayfa {pg}")
        self.setFillColor(C_DGRAY)
        self.drawRightString(w - 12*mm, 6.5*mm,
                             datetime.now().strftime('%d.%m.%Y'))


# ─── Markdown Satır Temizleyici ───────────────────────────────────────────────

def _escape(text: str) -> str:
    """ReportLab XML için güvenli kaçış + inline bold/italic dönüşümü."""
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # *italic*
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # `code`
    text = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', text)
    return text


def _strip_md_bold(text: str) -> str:
    """Saf metin — ** ve * kaldır (tablo hücresi raw parse için)."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    return text.strip()


# ─── Tablo Parser ─────────────────────────────────────────────────────────────

def _parse_md_table(lines: list[str]) -> list | None:
    """
    Markdown | tablo satırlarını 2D liste olarak döndürür.
    Separator satırını (|---|) atlar.
    """
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            break
        if re.match(r'^\|[-| :]+\|$', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cells)
    return rows if len(rows) >= 2 else None


def _md_table_to_rl(rows: list[str], page_width_mm: float = 181) -> Table:
    """Markdown tablo satırlarını ReportLab Table'a dönüştürür."""
    n_cols = max(len(r) for r in rows)
    col_w = (page_width_mm / n_cols) * mm

    data = []
    for i, row in enumerate(rows):
        cells = []
        for cell in row:
            raw = _strip_md_bold(cell)
            escaped = _escape(raw)
            style = S['th'] if i == 0 else S['td']
            cells.append(Paragraph(escaped, style))
        # Sütun eksikse boş doldur
        while len(cells) < n_cols:
            cells.append(Paragraph('', S['td']))
        data.append(cells)

    t = Table(data, colWidths=[col_w] * n_cols, repeatRows=1)
    t.setStyle(TableStyle([
        ('GRID',       (0, 0), (-1, -1), 0.4, C_MGRAY),
        ('BACKGROUND', (0, 0), (-1,  0), C_NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_LGRAY]),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


# ─── Kod Bloğu Renderer ───────────────────────────────────────────────────────

def _render_code_block(lines: list[str]) -> Table:
    """
    ASCII art veya preformatted satırları koyu arka planlı,
    monospace kutuda gösterir.  Satır başı boşlukları korunur.
    """
    safe_lines = []
    for line in lines:
        # XML kaçış (bold/italic işleme yok — ham gösterim)
        line = (line
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))
        # Baştaki boşlukları &nbsp; ile koru
        stripped = line.lstrip(' ')
        n_spaces = len(line) - len(stripped)
        safe_lines.append('&nbsp;' * n_spaces + stripped)

    content = '<br/>'.join(safe_lines) if safe_lines else '&nbsp;'
    p = Paragraph(content, S['code'])
    t = Table([[p]], colWidths=[181*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_CODE_BG),
        ('BOX',        (0, 0), (-1, -1), 0.5, C_ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


# ─── Kapak Sayfası ───────────────────────────────────────────────────────────

def _kapak_sayfasi() -> list:
    """Dökümanın kapak sayfası elementleri."""
    elems = []

    # Üst dolgu
    elems.append(Spacer(1, 30*mm))

    # Ana başlık bloğu
    header_data = [[
        Paragraph("EKLERİSTAN QMS", S['cover_title']),
    ]]
    sub_data = [[
        Paragraph("Sistem &amp; Modül Derin Analiz Rehberi", S['cover_sub']),
    ]]
    for d in [header_data, sub_data]:
        t = Table(d, colWidths=[181*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_NAVY),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elems.append(t)

    elems.append(Spacer(1, 8*mm))

    # Meta bilgi tablosu
    meta = [
        ["Versiyon", "6.0 — Kod Taramalı, Tam Kapsam"],
        ["Tarih", datetime.now().strftime("%d.%m.%Y")],
        ["Kapsam", "14 Modül · Tüm Alt Sekmeler · Tüm Butonlar"],
        ["Kaynak", ".antigravity/musbet/hafiza/sistem_modul_analizi.md"],
        ["Durum", "Onaylı — Emre Bey"],
    ]
    meta_data = []
    for key, val in meta:
        meta_data.append([
            Paragraph(f"<b>{_escape(key)}</b>", S['td']),
            Paragraph(_escape(val), S['td']),
        ])
    mt = Table(meta_data, colWidths=[40*mm, 141*mm])
    mt.setStyle(TableStyle([
        ('GRID',       (0, 0), (-1, -1), 0.4, C_MGRAY),
        ('BACKGROUND', (0, 0), (0, -1), C_LGRAY),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elems.append(mt)
    elems.append(Spacer(1, 10*mm))

    # Gizlilik notu
    gizli_data = [[Paragraph(
        "<b>⚠️ GİZLİ &amp; KURUMSAL KULLANIM</b><br/>"
        "Bu döküman EKLERİSTAN QMS'in tüm teknik mimarisini içermektedir. "
        "Sadece yetkili personel ve yapay zeka ajanlar tarafından kullanılabilir.",
        S['warn']
    )]]
    gt = Table(gizli_data, colWidths=[181*mm])
    gt.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, C_ORANGE),
        ('BACKGROUND', (0, 0), (-1, -1), C_WARN_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elems.append(gt)
    elems.append(PageBreak())
    return elems


# ─── Ana Parser ───────────────────────────────────────────────────────────────

def _md_to_elements(md_text: str) -> list:
    """
    Markdown metnini ReportLab Flowable listesine dönüştürür.
    Desteklenen yapılar:
      - # ## ### #### başlıklar
      - > blockquote
      - | tablo
      - ``` kod blokları
      - - bullet listeler
      - --- yatay çizgi / sayfa kırılımı (bölüm arası)
      - **bold** *italic* `inline code`
    """
    lines = md_text.split('\n')
    elems = []
    i = 0
    n = len(lines)

    # İçindekiler için bölüm sayacı
    section_major = 0

    while i < n:
        raw = lines[i]
        stripped = raw.strip()

        # ── Boş satır ──
        if not stripped:
            i += 1
            continue

        # ── Yatay çizgi --- ──
        if stripped in ('---', '***', '___') and len(stripped) >= 3:
            elems.append(HRFlowable(
                width="100%", thickness=0.5, color=C_MGRAY,
                spaceAfter=3, spaceBefore=3
            ))
            i += 1
            continue

        # ── Kod Bloğu ``` ──
        if stripped.startswith('```'):
            i += 1
            code_lines = []
            while i < n and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # kapanış ``` geç
            elems.append(Spacer(1, 1*mm))
            elems.append(_render_code_block(code_lines))
            elems.append(Spacer(1, 2*mm))
            continue

        # ── Markdown Tablosu ──
        if stripped.startswith('|'):
            table_lines = []
            while i < n and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            rows = _parse_md_table(table_lines)
            if rows:
                elems.append(Spacer(1, 1*mm))
                elems.append(_md_table_to_rl(rows))
                elems.append(Spacer(1, 2*mm))
            continue

        # ── Başlıklar ──
        if stripped.startswith('#### '):
            txt = _escape(stripped[5:])
            elems.append(Spacer(1, 1*mm))
            elems.append(Paragraph(txt, S['h4']))
            i += 1
            continue

        if stripped.startswith('### '):
            txt = _escape(stripped[4:])
            elems.append(Spacer(1, 2*mm))
            # Renkli sol çubuk efekti — tablo ile simüle
            bar = Table(
                [[Paragraph(txt, S['h3'])]],
                colWidths=[181*mm]
            )
            bar.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBEFORE', (0, 0), (0, -1), 3, C_ACCENT),
                ('BACKGROUND', (0, 0), (-1, -1), C_LGRAY),
            ]))
            elems.append(bar)
            i += 1
            continue

        if stripped.startswith('## '):
            txt = _escape(stripped[3:])
            # Sayfa kırılımı — her ## bölümü yeni sayfa
            elems.append(CondPageBreak(60*mm))
            bar = Table(
                [[Paragraph(txt, S['h2'])]],
                colWidths=[181*mm]
            )
            bar.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LINEBEFORE', (0, 0), (0, -1), 4, C_ORANGE),
                ('LINEBELOW', (0, -1), (-1, -1), 0.5, C_MGRAY),
            ]))
            elems.append(bar)
            elems.append(Spacer(1, 2*mm))
            i += 1
            continue

        if stripped.startswith('# '):
            txt = _escape(stripped[2:])
            section_major += 1
            elems.append(PageBreak())
            # Büyük bölüm başlığı
            bar = Table(
                [[Paragraph(txt, S['h1'])]],
                colWidths=[181*mm]
            )
            bar.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), C_NAVY),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elems.append(bar)
            elems.append(Spacer(1, 4*mm))
            i += 1
            continue

        # ── Blockquote > ──
        if stripped.startswith('> '):
            txt = _escape(stripped[2:])
            bq = Table(
                [[Paragraph(txt, S['blockquote'])]],
                colWidths=[175*mm]
            )
            bq.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), C_INFO_BG),
                ('LINEBEFORE', (0, 0), (0, -1), 3, C_ACCENT),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elems.append(bq)
            elems.append(Spacer(1, 1*mm))
            i += 1
            continue

        # ── Bullet listesi - ──
        if stripped.startswith('- ') or stripped.startswith('* '):
            txt = _escape(stripped[2:])
            elems.append(Paragraph(f"• {txt}", S['bullet']))
            i += 1
            continue

        # ── İçindekiler Satırı (TOC bağlantı satırı) ──
        if stripped.startswith('[') and '](' in stripped and stripped.endswith(')'):
            # [Başlık](#anchor) → sadece metin göster
            match = re.match(r'\[(.+?)\]\(.*?\)', stripped)
            if match:
                elems.append(Paragraph(f"• {_escape(match.group(1))}", S['toc_item']))
                i += 1
                continue

        # ── Numaralı liste 1. 2. ──
        if re.match(r'^\d+\.\s', stripped):
            txt = _escape(re.sub(r'^\d+\.\s+', '', stripped))
            elems.append(Paragraph(f"&nbsp;&nbsp;{txt}", S['bullet']))
            i += 1
            continue

        # ── Uyarı satırı ⚠️ veya ❌ ──
        if stripped.startswith(('⚠️', '❌', '✅')):
            txt = _escape(stripped)
            warn = Table(
                [[Paragraph(txt, S['warn'])]],
                colWidths=[181*mm]
            )
            warn.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), C_WARN_BG),
                ('BOX', (0, 0), (-1, -1), 0.5, C_ORANGE),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elems.append(warn)
            elems.append(Spacer(1, 1*mm))
            i += 1
            continue

        # ── İçindekiler başlığı (özel tanıma) ──
        if stripped == '## İÇİNDEKİLER':
            elems.append(CondPageBreak(60*mm))
            toc_bar = Table(
                [[Paragraph("İÇİNDEKİLER", S['h2'])]],
                colWidths=[181*mm]
            )
            toc_bar.setStyle(TableStyle([
                ('LINEBEFORE', (0, 0), (0, -1), 4, C_ORANGE),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elems.append(toc_bar)
            elems.append(Spacer(1, 2*mm))
            i += 1
            continue

        # ── Normal paragraf ──
        txt = _escape(stripped)
        if txt:
            elems.append(Paragraph(txt, S['body']))
        i += 1

    return elems


# ─── PDF Oluşturucu ───────────────────────────────────────────────────────────

def pdf_uret(md_path: str, output_path: str):
    """Markdown dosyasını oku, parse et, PDF olarak kaydet."""

    print(f"[INFO] Kaynak: {md_path}")
    print(f"[INFO] Çıktı : {output_path}")

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=portrait(A4),
        topMargin=18*mm,
        bottomMargin=18*mm,
        leftMargin=14*mm,
        rightMargin=14*mm,
        title="EKLERİSTAN QMS — Sistem & Modül Derin Analiz Rehberi v6.0",
        author="EKLERİSTAN QMS",
        subject="Modül Analiz Rehberi",
    )

    elements = []

    # 1. Kapak sayfası
    elements.extend(_kapak_sayfasi())

    # 2. İçindekiler sayfası
    elements.append(Spacer(1, 4*mm))
    elements.extend(_toc_sayfasi(md_text))
    elements.append(PageBreak())

    # 3. Asıl içerik
    elements.extend(_md_to_elements(md_text))

    # 4. Son sayfası
    elements.append(PageBreak())
    elements.extend(_son_sayfa())

    doc.build(elements, canvasmaker=AnalysisCanvas)
    print(f"[OK] PDF oluşturuldu: {output_path}")
    return output_path


# ─── İçindekiler Sayfası ─────────────────────────────────────────────────────

def _toc_sayfasi(md_text: str) -> list:
    """Markdown'dan başlık listesini çıkar, TOC tablosu oluştur."""
    elems = []

    toc_bar = Table(
        [[Paragraph("İÇİNDEKİLER", S['h1'])]],
        colWidths=[181*mm]
    )
    toc_bar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_NAVY),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elems.append(toc_bar)
    elems.append(Spacer(1, 5*mm))

    toc_data = []
    h1_count = 0
    h2_count = 0

    for line in md_text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            h1_count += 1
            h2_count = 0
            title = stripped[2:]
            toc_data.append([
                Paragraph(f"<b>{h1_count}.</b>", S['td']),
                Paragraph(f"<b>{_escape(title)}</b>", S['td']),
            ])
        elif stripped.startswith('## ') and not stripped.startswith('### '):
            h2_count += 1
            title = stripped[3:]
            toc_data.append([
                Paragraph(f"&nbsp;&nbsp;{h1_count}.{h2_count}", S['caption']),
                Paragraph(f"&nbsp;&nbsp;{_escape(title)}", S['caption']),
            ])

    if toc_data:
        toc_table = Table(toc_data, colWidths=[15*mm, 166*mm])
        toc_table.setStyle(TableStyle([
            ('GRID',       (0, 0), (-1, -1), 0, colors.white),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, C_LGRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elems.append(toc_table)

    return elems


# ─── Son Sayfa ────────────────────────────────────────────────────────────────

def _son_sayfa() -> list:
    elems = []
    elems.append(Spacer(1, 40*mm))

    footer_data = [[Paragraph(
        "<b>EKLERİSTAN QMS — Sistem &amp; Modül Derin Analiz Rehberi</b><br/>"
        f"Versiyon 6.0 | Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')}<br/>"
        "Bu döküman .antigravity/musbet/hafiza/sistem_modul_analizi.md kaynak dosyasından "
        "otomatik olarak üretilmiştir.<br/>"
        "anayasa.md + hafiza_ozeti.md ile birlikte Sistemin Ruhu'nu oluşturur.",
        S['caption']
    )]]
    ft = Table(footer_data, colWidths=[181*mm])
    ft.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_LGRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, C_MGRAY),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elems.append(ft)
    return elems


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    MD   = os.path.join(BASE, '.antigravity', 'musbet', 'hafiza', 'sistem_modul_analizi.md')
    OUT  = os.path.join(BASE, 'docs', 'EKLERISTAN_QMS_MODUL_STRATEJI_ANALIZI.pdf')

    if not os.path.exists(MD):
        print(f"[HATA] Kaynak dosya bulunamadı: {MD}")
        sys.exit(1)

    pdf_uret(MD, OUT)
