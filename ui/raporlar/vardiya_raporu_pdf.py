"""
Paylaşımlı Vardiya PDF Rapor Motoru (v1.0.0)
Hem Vardiya Yönetimi sayfasından hem Kurumsal Raporlama'dan çağrılır.
"""
import streamlit as st
import json
from datetime import date, timedelta

from logic.data_fetcher import run_query
from ui.raporlar.report_utils import _generate_base_html, _rapor_excel_export


def _vardiya_veri_cek(filtre_tipi, filtre_degeri, bas_tarih, bit_tarih):
    """Filtreli, onaylı vardiya verisi çeker."""
    where_parts = ["vp.onay_durumu = 'ONAYLANDI'"]
    if bas_tarih and bit_tarih:
        where_parts.append(f"vp.baslangic_tarihi <= '{bit_tarih}'")
        where_parts.append(f"vp.bitis_tarihi >= '{bas_tarih}'")
    if filtre_tipi == "Bölüm Bazlı" and filtre_degeri:
        safe = str(filtre_degeri).replace("'", "''")
        where_parts.append(f"COALESCE(d.ad, p.bolum) = '{safe}'")
    elif filtre_tipi == "Vardiya Bazlı" and filtre_degeri:
        safe = str(filtre_degeri).replace("'", "''")
        where_parts.append(f"vp.vardiya = '{safe}'")
    where_sql = " AND ".join(where_parts)
    return run_query(
        'SELECT p.ad_soyad as "Personel", p.gorev as "Gorev", '
        'COALESCE(d.ad, p.bolum, \'Tanımsız\') as "Bolum", '
        'vp.vardiya as "Vardiya", '
        'vp.baslangic_tarihi as "Baslangic", '
        'vp.bitis_tarihi as "Bitis" '
        "FROM personel_vardiya_programi vp "
        "JOIN ayarlar_kullanicilar p ON vp.personel_id = p.id "
        "LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id "
        f"WHERE {where_sql} ORDER BY Bolum, Vardiya, Personel"
    )


def _vardiya_html_olustur(df, filtre_tipi, filtre_degeri, bas_tarih, bit_tarih):
    """Kurumsal HTML vardiya çizelgesi oluşturur (_generate_base_html altyapısı)."""
    if df.empty:
        return None
    toplam_pers = df["Personel"].nunique()
    bolum_sayisi = df["Bolum"].nunique()
    vardiya_sayisi = df["Vardiya"].nunique()
    filtre_label = (
        "Tüm Fabrika" if filtre_tipi == "Tüm Fabrika"
        else f"{filtre_tipi}: {filtre_degeri}"
    )
    period = f"{bas_tarih} — {bit_tarih} | {filtre_label}"
    summary_cards = (
        f'<div class="ozet-kart toplam">Toplam Personel<br>'
        f'<strong>{toplam_pers}</strong></div>'
        f'<div class="ozet-kart onay">Bölüm Sayısı<br>'
        f'<strong>{bolum_sayisi}</strong></div>'
        f'<div class="ozet-kart" style="background:#fff3e0;color:#e65100;'
        f'border:1px solid #e65100;">Vardiya Tipi<br>'
        f'<strong>{vardiya_sayisi}</strong></div>'
    )
    rows_html = ""
    for bolum, grp_b in df.groupby("Bolum", sort=True):
        b_count = grp_b["Personel"].nunique()
        rows_html += (
            f'<tr style="background:#1a2744;color:white;">'
            f'<td colspan="5"><strong>🏭 {bolum} '
            f'({b_count} personel)</strong></td></tr>'
        )
        for vardiya, grp_v in grp_b.groupby("Vardiya", sort=True):
            rows_html += (
                f'<tr style="background:#e8eaf6;">'
                f'<td colspan="5"><em>⏰ {vardiya}</em></td></tr>'
            )
            for _, r in grp_v.iterrows():
                gorev = r.get("Gorev") or "-"
                rows_html += (
                    f'<tr><td>{r["Personel"]}</td>'
                    f'<td>{gorev}</td>'
                    f'<td>{r["Baslangic"]}</td>'
                    f'<td>{r["Bitis"]}</td>'
                    f'<td>{r["Vardiya"]}</td></tr>'
                )
    content = (
        "<table><thead><tr>"
        "<th>Personel Adı</th><th>Görev</th>"
        "<th>Başlangıç</th><th>Bitiş</th><th>Vardiya</th>"
        f"</tr></thead><tbody>{rows_html}</tbody></table>"
    )
    sigs = (
        '<div class="imza-kutu"><b>İnsan Kaynakları</b><br><br>İmza</div>'
        '<div class="imza-kutu"><b>Üretim Müdürü</b><br><br>İmza</div>'
        '<div class="imza-kutu"><b>Genel Müdür</b><br><br>İmza</div>'
    )
    return _generate_base_html(
        title="PERSONEL VARDİYA ÇİZELGESİ",
        doc_no="EKL-IK-R-VAR-001",
        period=period,
        summary_cards=summary_cards,
        content=content,
        signatures=sigs,
    )


def render_vardiya_pdf_raporu(engine, bas_tarih=None, bit_tarih=None, key_prefix="vpr"):
    """
    Paylaşımlı vardiya PDF raporu.
    bas_tarih/bit_tarih dışarıdan gelirse kullanılır (dispatcher);
    gelmezse kullanıcı kendi seçer (vardiya sayfası).
    """
    st.subheader("📄 Kurumsal PDF Vardiya Çizelgesi")

    # ── Kapsam Filtresi ──────────────────────────────────────────
    filtre_tipi = st.radio(
        "Rapor Kapsamı",
        ["Tüm Fabrika", "Bölüm Bazlı", "Vardiya Bazlı"],
        horizontal=True,
        key=f"{key_prefix}_filtre_tipi",
    )

    filtre_degeri = None
    if filtre_tipi == "Bölüm Bazlı":
        bolum_df = run_query(
            "SELECT DISTINCT COALESCE(d.ad, p.bolum) as ad "
            "FROM ayarlar_kullanicilar p "
            "LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id "
            "WHERE p.durum = 'AKTİF' ORDER BY ad"
        )
        if not bolum_df.empty:
            opts = [b for b in bolum_df.iloc[:, 0].tolist()
                    if b and str(b) not in ("None", "nan")]
            filtre_degeri = st.selectbox("Bölüm Seçin", opts,
                                         key=f"{key_prefix}_bolum")
    elif filtre_tipi == "Vardiya Bazlı":
        v_df = run_query(
            "SELECT tip_adi FROM vardiya_tipleri WHERE aktif = 1 ORDER BY sira_no"
        )
        v_opts = (v_df["tip_adi"].tolist() if not v_df.empty
                  else ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"])
        filtre_degeri = st.selectbox("Vardiya Seçin", v_opts,
                                     key=f"{key_prefix}_vardiya")

    # ── Tarih Aralığı ────────────────────────────────────────────
    if bas_tarih is None or bit_tarih is None:
        dc1, dc2 = st.columns(2)
        bas_tarih = dc1.date_input(
            "Başlangıç Tarihi",
            date.today() - timedelta(days=30),
            key=f"{key_prefix}_bas",
        )
        bit_tarih = dc2.date_input(
            "Bitiş Tarihi",
            date.today() + timedelta(days=30),
            key=f"{key_prefix}_bit",
        )
    else:
        st.caption(f"📅 Dönem: {bas_tarih} — {bit_tarih}")

    # ── Rapor Üret ───────────────────────────────────────────────
    if not st.button("📄 Raporu Oluştur", type="primary",
                     width="stretch", key=f"{key_prefix}_btn"):
        return

    with st.spinner("Rapor hazırlanıyor..."):
        df = _vardiya_veri_cek(filtre_tipi, filtre_degeri,
                               bas_tarih, bit_tarih)

    if df.empty:
        st.warning("⚠️ Seçilen kriterlere uygun onaylı vardiya kaydı bulunamadı.")
        return

    html = _vardiya_html_olustur(
        df, filtre_tipi, filtre_degeri,
        str(bas_tarih), str(bit_tarih)
    )

    # ── İndirme ──────────────────────────────────────────────────
    col_pdf, col_xls = st.columns(2)
    with col_pdf:
        html_json = json.dumps(html)
        pdf_js = (
            "<script>function p(){var w=window.open('','_blank');"
            f"w.document.write({html_json});w.document.close();"
            "setTimeout(function(){w.print();},600);}</script>"
            "<button onclick='p()' style='width:100%;padding:10px;"
            "background:#8B0000;color:white;border:none;border-radius:5px;"
            "cursor:pointer;font-size:14px;'>🖨️ PDF Kaydet (Yazdır)</button>"
        )
        st.components.v1.html(pdf_js, height=60)
    with col_xls:
        _rapor_excel_export(st, df, None, "Vardiya_Cizelgesi",
                            bas_tarih, bit_tarih)

    st.info(
        "💡 'PDF Kaydet' butonuna tıklayın → tarayıcı yazdırma ekranında "
        "'PDF olarak kaydet' seçeneğini kullanın."
    )

    # ── Önizleme ─────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        f"📊 {df['Personel'].nunique()} ayarlar_kullanicilar | "
        f"{df['Bolum'].nunique()} bölüm | "
        f"{df['Vardiya'].nunique()} vardiya tipi"
    )
    st.dataframe(df, width="stretch", hide_index=True)
