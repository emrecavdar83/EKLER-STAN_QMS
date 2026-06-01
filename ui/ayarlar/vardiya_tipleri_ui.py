"""
Vardiya Tipleri CRUD Ekranı (v8.0.0)
Ayarlar > Vardiya Tipleri sekmesinde kullanılır.

Anayasa Uyumu:
  - Maks 30 satır/fonksiyon (Madde 3)
  - Türkçe snake_case (Madde 2)
  - Sıfır hardcode (Madde 1) — vardiya isimleri DB'den
  - Audit trail: vardiya_degisim_loglari yerine sistem_loglari (genel ayar değişikliği)
"""
import re
import streamlit as st
import pandas as pd
from sqlalchemy import text


_SAAT_REGEX = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _saat_dogrula(saat: str) -> bool:
    """'07:00' ✓, '7:0' ✗, '24:00' ✗"""
    return bool(_SAAT_REGEX.match(str(saat or "").strip()))


def _vardiya_listele(engine) -> pd.DataFrame:
    """Tüm vardiya tiplerini (aktif+pasif) sira_no'ya göre döner."""
    sql = text(
        "SELECT id, tip_adi, baslangic_saati, bitis_saati, sira_no, aktif "
        "FROM vardiya_tipleri ORDER BY aktif DESC, sira_no, id"
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()
    return pd.DataFrame(rows, columns=[
        "id", "tip_adi", "baslangic_saati", "bitis_saati", "sira_no", "aktif"
    ])


def _yeni_vardiya_ekle(engine, baslangic: str, bitis: str, sira: int) -> tuple:
    """Yeni saat formatlı vardiya ekler. tip_adi otomatik üretilir."""
    if not (_saat_dogrula(baslangic) and _saat_dogrula(bitis)):
        return False, "Saat formatı geçersiz (HH:MM olmalı)"
    tip_adi = f"{baslangic}-{bitis}"
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO vardiya_tipleri (tip_adi, baslangic_saati, bitis_saati, sira_no, aktif) "
                "VALUES (:t, :b, :e, :s, 1)"
            ), {"t": tip_adi, "b": baslangic, "e": bitis, "s": sira})
        return True, f"Eklendi: {tip_adi}"
    except Exception as e:
        return False, f"Hata: {str(e)[:120]}"


def _vardiya_guncelle(engine, vid: int, baslangic: str, bitis: str,
                      sira: int, aktif: int) -> tuple:
    """Mevcut tipi günceller, tip_adi otomatik yenilenir."""
    if not (_saat_dogrula(baslangic) and _saat_dogrula(bitis)):
        return False, "Saat formatı geçersiz"
    tip_adi = f"{baslangic}-{bitis}"
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE vardiya_tipleri SET tip_adi=:t, baslangic_saati=:b, "
                "bitis_saati=:e, sira_no=:s, aktif=:a WHERE id=:i"
            ), {"t": tip_adi, "b": baslangic, "e": bitis,
                "s": sira, "a": aktif, "i": vid})
        return True, "Güncellendi"
    except Exception as e:
        return False, f"Hata: {str(e)[:120]}"


def _yeni_form_render(engine):
    """Yeni vardiya ekleme formu (üst panel)."""
    st.markdown("##### ➕ Yeni Vardiya Tipi Ekle")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    bas = c1.text_input("Başlangıç (HH:MM)", value="07:00", key="vt_yeni_bas")
    bit = c2.text_input("Bitiş (HH:MM)", value="15:00", key="vt_yeni_bit")
    sira = c3.number_input("Sıra No", min_value=1, max_value=99, value=10, key="vt_yeni_sira")
    if c4.button("Ekle", type="primary", width="stretch", key="vt_yeni_ekle"):
        ok, msg = _yeni_vardiya_ekle(engine, bas.strip(), bit.strip(), int(sira))
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


def _liste_editor_render(engine, df: pd.DataFrame):
    """Vardiya tipleri listesi — data_editor ile düzenleme."""
    st.markdown("##### 📋 Mevcut Vardiya Tipleri")
    if df.empty:
        st.info("Henüz vardiya tipi yok. Yukarıdan ekleyin.")
        return
    edited = st.data_editor(
        df,
        column_config={
            "id": None,
            "tip_adi": st.column_config.TextColumn("Tip Adı (Otomatik)", disabled=True),
            "baslangic_saati": st.column_config.TextColumn("Başlangıç", help="HH:MM"),
            "bitis_saati": st.column_config.TextColumn("Bitiş", help="HH:MM"),
            "sira_no": st.column_config.NumberColumn("Sıra", min_value=1, max_value=99),
            "aktif": st.column_config.CheckboxColumn("Aktif", default=True),
        },
        width="stretch", hide_index=True, key="vt_editor"
    )
    if st.button("💾 Değişiklikleri Kaydet", type="primary", key="vt_kaydet"):
        _toplu_guncelle(engine, df, edited)


def _toplu_guncelle(engine, eski: pd.DataFrame, yeni: pd.DataFrame):
    """data_editor değişikliklerini DB'ye yansıt."""
    basari, hata = 0, []
    for _, row in yeni.iterrows():
        eski_row = eski[eski['id'] == row['id']].iloc[0] if len(eski[eski['id'] == row['id']]) else None
        if eski_row is None:
            continue
        if (str(row['baslangic_saati']) != str(eski_row['baslangic_saati'])
                or str(row['bitis_saati']) != str(eski_row['bitis_saati'])
                or int(row['sira_no']) != int(eski_row['sira_no'])
                or int(row['aktif']) != int(eski_row['aktif'])):
            ok, msg = _vardiya_guncelle(
                engine, int(row['id']),
                str(row['baslangic_saati']).strip(),
                str(row['bitis_saati']).strip(),
                int(row['sira_no']), int(row['aktif'])
            )
            if ok:
                basari += 1
            else:
                hata.append(f"ID {row['id']}: {msg}")
    if basari:
        st.success(f"✅ {basari} kayıt güncellendi")
    if hata:
        for h in hata:
            st.error(h)
    if basari and not hata:
        st.rerun()


def render_vardiya_tipleri_tab(engine):
    """Ayarlar > Vardiya Tipleri sekmesi ana giriş noktası."""
    st.subheader("⏰ Vardiya Tipleri Yönetimi")
    st.caption(
        "Sistem genelinde kullanılan vardiya saat aralıklarını buradan yönetin. "
        "Tip adı otomatik **HH:MM-HH:MM** formatındadır."
    )
    try:
        from logic.auth_logic import eylem_yapabilir_mi
        if not eylem_yapabilir_mi('ayarlar', 'duzenleme'):
            st.error("⛔ Bu sayfa için düzenleme yetkin yok.")
            return
    except Exception:
        pass

    df = _vardiya_listele(engine)
    _yeni_form_render(engine)
    st.divider()
    _liste_editor_render(engine, df)
