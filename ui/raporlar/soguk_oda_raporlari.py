"""
Soğuk Zincir (SOSTS) Kurumsal Raporlama Modülü (v2.0.0)
Anayasa Madde 33: report-wrapper-table mimarisi ile kurumsal PDF desteği.
Anayasa Madde 3: Max 30 satır fonksiyonlar.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import plotly.express as px
import pytz

from logic.data_fetcher import run_query
from ui.raporlar.report_utils import (
    _rapor_excel_export, _get_personnel_display_map,
    _generate_base_html, get_istanbul_time
)
from ui.raporlar.islem_raporlari import render_islem_gecmisi_tab
from soguk_oda_utils import get_matrix_data, get_trend_data


# ─────────────────────────────────────────────────────────────────────────────
# ANA ORKESTRATÖR
# ─────────────────────────────────────────────────────────────────────────────

def render_soguk_oda_sub_module(engine, bas_tarih, bit_tarih):
    st.subheader("❄️ Soğuk Zincir Takip Raporları")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Günlük İzleme Matrisi",
        "📄 Kurumsal PDF Raporu",
        "📈 Sıcaklık Trend Analizi",
        "🔍 İşlem Geçmişi"
    ])

    with tab1:
        _render_soguk_oda_izleme(engine, bas_tarih, bit_tarih)

    with tab2:
        _render_soguk_oda_pdf_raporu(engine, bas_tarih, bit_tarih)

    with tab3:
        _render_soguk_oda_trend(engine)

    with tab4:
        render_islem_gecmisi_tab(engine, "soguk_oda", bas_tarih, bit_tarih)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: GÜNLÜK İZLEME MATRİSİ
# ─────────────────────────────────────────────────────────────────────────────

def _render_soguk_oda_izleme(engine, bas_tarih, bit_tarih):
    st.info("❄️ Günlük Sıcaklık İzleme (Matris Görünümü)")

    df_matris = get_matrix_data(engine, bas_tarih, bit_tarih)
    if df_matris.empty:
        st.warning("Bu tarih için henüz planlanmış ölçüm bulunmuyor.")
        return

    st.dataframe(df_matris, width="stretch", hide_index=True)
    _rapor_excel_export(st, df_matris, None, "Soguk_Oda_İzleme", bas_tarih, bit_tarih)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: KURUMSAL PDF RAPORU
# ─────────────────────────────────────────────────────────────────────────────

def _soguk_zincir_veri_cek(bas_tarih, bit_tarih, oda_id=None):
    """Soğuk zincir ölçüm verisini kurumsal rapor için çeker."""
    where_oda = f"AND m.oda_id = {int(oda_id)}" if oda_id else ""
    return run_query(f"""
        SELECT
            o.oda_adi,
            o.min_sicaklik, o.max_sicaklik,
            m.olcum_zamani,
            m.sicaklik_degeri,
            m.sapma_var_mi,
            m.sapma_aciklamasi,
            m.kaydeden_kullanici,
            m.qr_ile_girildi
        FROM sicaklik_olcumleri m
        JOIN soguk_odalar o ON m.oda_id = o.id
        WHERE m.olcum_zamani::date BETWEEN '{bas_tarih}' AND '{bit_tarih}'
        {where_oda}
        ORDER BY o.oda_adi, m.olcum_zamani
    """)


def _soguk_zincir_ozet_hesapla(df):
    """Rapor özet kartları için metrikleri hesaplar."""
    toplam = len(df)
    sapma_sayisi = int(df['sapma_var_mi'].sum()) if 'sapma_var_mi' in df.columns else 0
    uygun = toplam - sapma_sayisi
    oda_sayisi = df['oda_adi'].nunique() if not df.empty else 0
    uyum_orani = round((uygun / toplam * 100), 1) if toplam > 0 else 0
    return toplam, sapma_sayisi, uygun, oda_sayisi, uyum_orani


def _soguk_zincir_ozet_kartlari(toplam, sapma, uygun, oda_sayisi, uyum_orani):
    """HTML özet kartlarını üretir."""
    return (
        f'<div class="ozet-kart toplam">Toplam Ölçüm<br>'
        f'<strong>{toplam}</strong></div>'
        f'<div class="ozet-kart onay">Uygun ✅<br>'
        f'<strong>{uygun}</strong></div>'
        f'<div class="ozet-kart red">Sapma ⚠️<br>'
        f'<strong>{sapma}</strong></div>'
        f'<div class="ozet-kart" style="background:#e3f2fd;color:#0d47a1;'
        f'border:1px solid #0d47a1;">Uyum Oranı<br>'
        f'<strong>%{uyum_orani}</strong></div>'
    )


def _soguk_zincir_tablo_satirlari(df, p_map):
    """Oda bazlı gruplandırılmış HTML tablo satırlarını üretir."""
    rows = ""
    for oda, grp in df.groupby("oda_adi", sort=True):
        oda_sapma = int(grp['sapma_var_mi'].sum())
        oda_uyum = round(((len(grp) - oda_sapma) / len(grp) * 100), 1) if len(grp) > 0 else 0
        min_s = grp.iloc[0]['min_sicaklik']
        max_s = grp.iloc[0]['max_sicaklik']

        rows += (
            f'<tr style="background:#1a2744;color:white;">'
            f'<td colspan="6"><strong>❄️ {oda} '
            f'(Limit: {min_s}°C — {max_s}°C | '
            f'{len(grp)} ölçüm | Uyum: %{oda_uyum})'
            f'</strong></td></tr>'
        )
        rows += _soguk_zincir_oda_satirlari(grp, p_map)
    return rows


def _soguk_zincir_oda_satirlari(grp, p_map):
    """Tek bir odanın ölçüm satırlarını HTML olarak üretir."""
    rows = ""
    for _, r in grp.iterrows():
        sicaklik = r['sicaklik_degeri']
        sapma = r['sapma_var_mi']
        zaman = str(r['olcum_zamani'])[:-3] if r['olcum_zamani'] else "-"
        kullanici = str(r.get('kaydeden_kullanici', '-'))
        kullanici_display = p_map.get(kullanici, kullanici)
        qr = "📱 QR" if r.get('qr_ile_girildi') else "✍️ Manuel"

        if sapma:
            badge = '<span class="badge bg-red">SAPMA</span>'
            aciklama = str(r.get('sapma_aciklamasi', '')) or '-'
        else:
            badge = '<span class="badge bg-green">UYGUN</span>'
            aciklama = "-"

        rows += (
            f'<tr><td>{zaman}</td>'
            f'<td style="text-align:center;font-weight:bold;">{sicaklik}°C</td>'
            f'<td style="text-align:center;">{badge}</td>'
            f'<td>{aciklama}</td>'
            f'<td>{kullanici_display}</td>'
            f'<td style="text-align:center;">{qr}</td></tr>'
        )
    return rows


def _soguk_zincir_html_olustur(df, bas_tarih, bit_tarih, p_map, oda_filtre="Tüm Odalar"):
    """Kurumsal HTML raporu üretir (_generate_base_html altyapısı)."""
    toplam, sapma, uygun, oda_sayisi, uyum_orani = _soguk_zincir_ozet_hesapla(df)
    cards = _soguk_zincir_ozet_kartlari(toplam, sapma, uygun, oda_sayisi, uyum_orani)
    tablo_satirlari = _soguk_zincir_tablo_satirlari(df, p_map)

    content = (
        '<table><thead><tr>'
        '<th>Ölçüm Zamanı</th><th>Sıcaklık</th>'
        '<th>Durum</th><th>Sapma Açıklaması</th>'
        '<th>Personel</th><th>Giriş Tipi</th>'
        f'</tr></thead><tbody>{tablo_satirlari}</tbody></table>'
    )

    sigs = (
        '<div class="imza-kutu"><b>Kalite Güvence</b><br><br>İmza</div>'
        '<div class="imza-kutu"><b>Üretim Müdürü</b><br><br>İmza</div>'
        '<div class="imza-kutu"><b>Depo Sorumlusu</b><br><br>İmza</div>'
    )

    period = f"{bas_tarih} — {bit_tarih} | {oda_filtre}"

    return _generate_base_html(
        title="SOĞUK ZİNCİR SICAKLIK İZLEME RAPORU",
        doc_no="EKL-KG-R-SZ-001",
        period=period,
        summary_cards=cards,
        content=content,
        signatures=sigs,
    )


def _render_soguk_oda_pdf_raporu(engine, bas_tarih, bit_tarih):
    """Kurumsal PDF raporu render fonksiyonu."""
    st.subheader("📄 Kurumsal Soğuk Zincir PDF Raporu")

    # Oda Filtresi
    rooms = run_query("SELECT id, oda_adi FROM soguk_odalar WHERE durum = 'AKTİF' ORDER BY oda_adi")
    oda_opts = {"all": "Tüm Odalar"}
    if not rooms.empty:
        oda_opts.update(dict(zip(rooms['id'].astype(str), rooms['oda_adi'])))

    sel_oda = st.selectbox(
        "Oda Seçimi", list(oda_opts.keys()),
        format_func=lambda x: oda_opts[x],
        key="sz_pdf_oda"
    )

    oda_id = None if sel_oda == "all" else int(sel_oda)
    oda_label = oda_opts[sel_oda]

    if not st.button("📄 Raporu Oluştur", type="primary", width="stretch", key="sz_pdf_btn"):
        return

    with st.spinner("Soğuk zincir raporu hazırlanıyor..."):
        df = _soguk_zincir_veri_cek(bas_tarih, bit_tarih, oda_id)

    if df.empty:
        st.warning("⚠️ Seçilen tarih ve oda için sıcaklık kaydı bulunamadı.")
        return

    p_map = _get_personnel_display_map(run_query, engine)
    html = _soguk_zincir_html_olustur(df, bas_tarih, bit_tarih, p_map, oda_label)

    # PDF ve Excel İndirme
    _render_indirme_butonlari(html, df, bas_tarih, bit_tarih, oda_label)

    # Önizleme Metrikleri
    toplam, sapma, uygun, oda_sayisi, uyum_orani = _soguk_zincir_ozet_hesapla(df)
    _render_onizleme(df, toplam, sapma, uygun, uyum_orani)


def _render_indirme_butonlari(html, df, bas_tarih, bit_tarih, oda_label):
    """PDF ve Excel indirme butonlarını render eder."""
    col_pdf, col_xls = st.columns(2)
    with col_pdf:
        html_json = json.dumps(html)
        pdf_js = (
            "<script>function p(){var w=window.open('','_blank');"
            f"w.document.write({html_json});w.document.close();"
            "setTimeout(function(){w.print();},600);}</script>"
            "<button onclick='p()' style='width:100%;padding:10px;"
            "background:#0d47a1;color:white;border:none;border-radius:5px;"
            "cursor:pointer;font-size:14px;'>🖨️ PDF Kaydet (Yazdır)</button>"
        )
        st.components.v1.html(pdf_js, height=60)
    with col_xls:
        safe_name = oda_label.replace(" ", "_")
        _rapor_excel_export(st, df, None, f"Soguk_Zincir_{safe_name}", bas_tarih, bit_tarih)

    st.info(
        "💡 'PDF Kaydet' butonuna tıklayın → tarayıcı yazdırma ekranında "
        "'PDF olarak kaydet' seçeneğini kullanın."
    )


def _render_onizleme(df, toplam, sapma, uygun, uyum_orani):
    """Rapor önizleme metriklerini ve tablosunu render eder."""
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Ölçüm", toplam)
    m2.metric("Uygun ✅", uygun)
    m3.metric("Sapma ⚠️", sapma)
    m4.metric("Uyum Oranı", f"%{uyum_orani}")

    # Görsel olarak sapmaları kırmızı ile göster
    display_df = df[['oda_adi', 'olcum_zamani', 'sicaklik_degeri', 'sapma_var_mi', 'kaydeden_kullanici']].copy()
    display_df.columns = ['Oda', 'Zaman', 'Sıcaklık (°C)', 'Sapma', 'Personel']
    display_df['Sapma'] = display_df['Sapma'].map({1: '⚠️ SAPMA', 0: '✅ Uygun'})
    st.dataframe(display_df, width="stretch", hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: SICAKLIK TREND ANALİZİ
# ─────────────────────────────────────────────────────────────────────────────

def _render_soguk_oda_trend(engine):
    st.subheader("📈 Sıcaklık Trend Analizi")
    rooms = run_query("SELECT id, oda_adi FROM soguk_odalar WHERE durum = 'AKTİF'")
    if rooms.empty:
        st.info("Kayıtlı aktif oda bulunamadı.")
        return

    target = st.selectbox(
        "Oda Seçiniz", rooms['id'],
        format_func=lambda x: rooms[rooms['id'] == x]['oda_adi'].iloc[0],
        key="sz_trend_oda"
    )
    df = get_trend_data(engine, target)

    if not df.empty:
        oda_adi = rooms[rooms['id'] == target]['oda_adi'].iloc[0]
        min_s = df.iloc[0]['min_sicaklik']
        max_s = df.iloc[0]['max_sicaklik']

        fig = px.line(
            df, x='olcum_zamani', y='sicaklik_degeri',
            title=f"{oda_adi} — Son 30 Gün Sıcaklık Trendi"
        )
        # Limit çizgileri
        fig.add_hline(y=min_s, line_dash="dash", line_color="blue",
                      annotation_text=f"Alt Limit ({min_s}°C)")
        fig.add_hline(y=max_s, line_dash="dash", line_color="red",
                      annotation_text=f"Üst Limit ({max_s}°C)")
        fig.update_layout(
            yaxis_title="Sıcaklık (°C)",
            xaxis_title="Zaman",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Kayıtlı trend verisi bulunamadı.")
