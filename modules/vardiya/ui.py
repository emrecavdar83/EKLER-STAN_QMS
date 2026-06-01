"""
Vardiya Modülü UI Katmanı (v8.0.0)

Yeni Akış:
  1. Plan Tipi (HAFTALIK / GUNLUK) — S8-c
  2. Tarih Aralığı
  3. Bölüm Seçimi — tüm kullanıcılar için aktif (S4-a)
  4. Personel Seçimi — checkbox per satır (S5-b)
  5. Vardiya + İzin Girişi — saat formatlı + bit-mask
  6. Onaya Gönder / Taslak Kaydet
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text

from modules.vardiya.logic import (
    get_personnel_for_shift_management, save_shift_plan, approve_shifts
)
from logic.data_fetcher import (
    get_department_options_hierarchical, get_all_sub_department_ids
)
from logic.vardiya_helper import (
    get_aktif_vardiyalar, izin_encode, izin_decode, izin_str, izin_multiselect
)


def render_vardiya_module(engine):
    """Operasyonel Vardiya Yönetimi ana giriş noktası."""
    st.title("📅 Operasyonel Vardiya Yönetimi (v8.0)")
    st.info(
        "Yeni: Saat formatlı vardiyalar (07:00-15:00), bit-mask haftalık izin, "
        "esnek plan tipi (Haftalık/Günlük)."
    )
    u_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper().strip()
    u_dept_id = st.session_state.get('user_dept_id', None)
    active_filter_ids = _bolum_secimi_render(u_rol, u_dept_id)

    tabs = st.tabs([
        "✍️ Vardiya Yaz",
        "🚦 Onay Bekleyenler",
        "📊 Vardiya Raporu (Servis Detaylı)",
        "📄 Kurumsal PDF Raporu",
    ])
    with tabs[0]:
        _render_shift_entry(engine, u_rol, active_filter_ids)
    with tabs[1]:
        _render_approval_queue(engine, u_rol)
    with tabs[2]:
        _render_shift_report(engine, u_rol, active_filter_ids)
    with tabs[3]:
        from ui.raporlar.vardiya_raporu_pdf import render_vardiya_pdf_raporu
        render_vardiya_pdf_raporu(engine, key_prefix="vpr_vardiya")


def _bolum_secimi_render(u_rol, u_dept_id):
    """v8.0 (S4-a): TÜM kullanıcılar için bölüm seçim kutusu (yetki dahilinde)."""
    dept_options = get_department_options_hierarchical()
    if u_rol == "ADMIN":
        secim = st.selectbox(
            "🏢 Bölüm Seçiniz", options=list(dept_options.keys()),
            format_func=lambda x: dept_options.get(x, "Tüm Fabrika"),
            index=0, key="vardiya_dept_admin"
        )
        if int(secim) > 0:
            return get_all_sub_department_ids(secim)
        return None
    if not u_dept_id:
        st.warning("⚠️ Departman atamanız yok — admin ile iletişime geçin.")
        return None
    izinli_ids = get_all_sub_department_ids(u_dept_id)
    izinli_options = {i: dept_options.get(i, f"Bölüm-{i}") for i in izinli_ids}
    keys = list(izinli_options.keys())
    secim = st.selectbox(
        "🏢 Plan Yapılacak Bölüm", options=keys,
        format_func=lambda x: izinli_options.get(x, "?"),
        index=keys.index(u_dept_id) if u_dept_id in keys else 0,
        key="vardiya_dept_user"
    )
    return get_all_sub_department_ids(secim)


def _plan_tipi_ve_tarih_render():
    """Plan tipi (HAFTALIK/GUNLUK) + tarih aralığı."""
    c1, c2, c3 = st.columns([1, 1, 1])
    plan_tipi = c1.radio(
        "📋 Plan Tipi", options=["HAFTALIK", "GUNLUK"],
        format_func=lambda x: "Haftalık" if x == "HAFTALIK" else "Günlük",
        horizontal=True, key="v_plan_tipi"
    )
    bas = c2.date_input("Başlangıç Tarihi", datetime.now(), key="v_bas")
    bit = c3.date_input("Bitiş Tarihi", datetime.now() + timedelta(days=6), key="v_bit")
    return plan_tipi, bas, bit


def _render_shift_entry(engine, u_rol, u_dept):
    """Vardiya yaz sekmesi — yeni akış."""
    st.subheader("✍️ Personel Vardiya Girişi")
    plan_tipi, start_date, end_date = _plan_tipi_ve_tarih_render()
    p_df = get_personnel_for_shift_management(engine, dept_id=u_dept, user_rol=u_rol)
    if p_df.empty:
        st.warning("Bu bölüme ait aktif personel bulunamadı.")
        return
    edited = _personel_data_editor(p_df)
    secili_df = edited[edited['plan_yap'] == True]  # noqa: E712
    if secili_df.empty:
        st.info("ℹ️ Plan yazmak istediğin personelleri ✓ ile işaretle.")
        return
    izin_bm = _toplu_izin_widget(len(secili_df))
    _onizleme_goster(plan_tipi, start_date, end_date, izin_bm, len(secili_df))
    _kaydet_butonlari(engine, secili_df, plan_tipi, start_date, end_date, izin_bm)


def _personel_data_editor(p_df):
    """Personel listesi data_editor — checkbox + vardiya seçimi."""
    from logic.vardiya_helper import izin_str
    aktif_v = get_aktif_vardiyalar()
    p_df = p_df.copy()
    p_df['plan_yap'] = False
    p_df['vardiya'] = aktif_v[0] if aktif_v else ""
    p_df['aciklama'] = ""
    # Bit-mask'ı okunabilir stringe dönüştür
    p_df['izin_gunu_str'] = p_df['izin_gunleri'].apply(lambda x: izin_str(x) if pd.notnull(x) else "-")
    
    return st.data_editor(
        p_df,
        column_config={
            "id": None,
            "departman_adi": None,
            "bolum": None,
            "izin_gunleri": None,
            "plan_yap": st.column_config.CheckboxColumn("✓", default=False, width="small"),
            "ad_soyad": st.column_config.TextColumn("Personel", disabled=True, width="medium"),
            "izin_gunu_str": st.column_config.TextColumn("📅 Sabit İzin Günü", disabled=True, width="medium"),
            "gorev": st.column_config.TextColumn("Görev", disabled=True),
            "servis_duragi": st.column_config.TextColumn("🚌 Servis", disabled=True),
            "vardiya": st.column_config.SelectboxColumn(
                "⏰ Vardiya", options=aktif_v, required=True
            ),
            "aciklama": st.column_config.TextColumn("💬 Notlar"),
        },
        width="stretch", hide_index=True, key="v_editor_v2"
    )


def _toplu_izin_widget(n_secili):
    """Seçili personeller için toplu izin günü seçimi."""
    st.markdown(f"##### 📅 Haftalık İzin Günleri (Seçili {n_secili} personel için)")
    return izin_multiselect(label="İzin Günleri", key="v_izin_toplu", mevcut_bitmask=0)


def _onizleme_goster(plan_tipi, start, end, izin_bm, n_personel):
    """Kullanıcıya kaç kayıt yazılacağının önizlemesi."""
    from logic.vardiya_helper import gun_izinli_mi, izin_str
    if plan_tipi == "HAFTALIK":
        st.info(
            f"📝 **Haftalık Plan**: {n_personel} personel × 1 kayıt = "
            f"**{n_personel} kayıt** yazılacak. "
            f"İzin günleri: {izin_str(izin_bm)}"
        )
        return
    toplam_gun = (end - start).days + 1
    calisan_gun, izinli_gun = 0, 0
    cur = start
    while cur <= end:
        if gun_izinli_mi(izin_bm, cur.weekday()):
            izinli_gun += 1
        else:
            calisan_gun += 1
        cur += timedelta(days=1)
    st.info(
        f"📝 **Günlük Plan**: {toplam_gun} günlük aralık → "
        f"{calisan_gun} çalışma günü, {izinli_gun} izin günü. "
        f"{n_personel} personel × {calisan_gun} gün = "
        f"**{n_personel * calisan_gun} kayıt** yazılacak."
    )


def _kaydet_butonlari(engine, secili_df, plan_tipi, start, end, izin_bm):
    """Onaya Gönder / Taslak Kaydet butonları."""
    c1, c2 = st.columns(2)
    if c1.button("🚀 Onaya Gönder", type="primary", width="stretch", key="v_gonder"):
        _kaydet(engine, secili_df, plan_tipi, start, end, izin_bm, "ONAY BEKLIYOR")
    if c2.button("💾 Taslak Kaydet", width="stretch", key="v_taslak"):
        _kaydet(engine, secili_df, plan_tipi, start, end, izin_bm, "TASLAK")


def _haftalik_records(secili_df, start, end, izin_bm, durum):
    """HAFTALIK plan: tek kayıt, tarih aralığı + bit-mask izin."""
    records = []
    for _, row in secili_df.iterrows():
        records.append({
            "personel_id": int(row['id']),
            "baslangic_tarihi": str(start),
            "bitis_tarihi": str(end),
            "vardiya": str(row['vardiya']),
            "izin_gunleri": int(izin_bm),
            "plan_tipi": "HAFTALIK",
            "aciklama": str(row.get('aciklama', '') or ''),
            "durum": durum,
        })
    return records


def _gunluk_records(secili_df, start, end, izin_bm, durum):
    """GUNLUK plan: tarih aralığındaki her gün için ayrı kayıt.
    İzin gününe denk gelen günlerde kayıt YAZILMAZ (atlanır)."""
    from logic.vardiya_helper import gun_izinli_mi
    records = []
    current = start
    while current <= end:
        if not gun_izinli_mi(izin_bm, current.weekday()):
            for _, row in secili_df.iterrows():
                records.append({
                    "personel_id": int(row['id']),
                    "baslangic_tarihi": str(current),
                    "bitis_tarihi": str(current),
                    "vardiya": str(row['vardiya']),
                    "izin_gunleri": 0,
                    "plan_tipi": "GUNLUK",
                    "aciklama": str(row.get('aciklama', '') or ''),
                    "durum": durum,
                })
        current += timedelta(days=1)
    return records


def _kaydet(engine, secili_df, plan_tipi, start, end, izin_bm, durum):
    """Vardiya kayıtlarını DB'ye yazar (HAFTALIK / GUNLUK)."""
    if plan_tipi == "GUNLUK":
        records = _gunluk_records(secili_df, start, end, izin_bm, durum)
    else:
        records = _haftalik_records(secili_df, start, end, izin_bm, durum)
    if not records:
        st.warning("⚠️ Yazılacak kayıt yok (tüm günler izinli olabilir).")
        return
    success, msg = save_shift_plan(engine, records, st.session_state.get('user_id', 0))
    if success:
        st.success(f"✅ {len(records)} kayıt {durum} ({plan_tipi}) durumunda kaydedildi.")
        st.rerun()
    else:
        st.error(f"❌ Hata: {msg}")


def _render_approval_queue(engine, u_rol):
    """Onay bekleyenler — sadece yetkili amirler görür."""
    st.subheader("🚦 Onay Bekleyen Vardiya Planları")
    if u_rol not in ['ADMIN', 'MÜDÜR', 'KOORDİNATÖR / ŞEF']:
        st.warning("Bu alanı sadece onay yetkisi olan amirler görebilir.")
        return
    u_dept_id = st.session_state.get('user_dept_id', None)
    pending = _bekleyen_listeyi_cek(engine, u_rol, u_dept_id)
    if pending.empty:
        st.info("Şu anda onay bekleyen plan yok.")
        return
    if 'izin_gunleri' in pending.columns:
        pending['izin_str'] = pending['izin_gunleri'].apply(izin_str)
    secili = st.multiselect(
        "Onaylanacak Kayıtları Seçiniz", pending['id'].tolist(),
        format_func=lambda x: f"ID: {x}"
    )
    if st.button("✅ Seçilenleri Onayla", width="stretch"):
        if secili:
            ok, msg = approve_shifts(engine, secili, st.session_state.get('user_id', 0))
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
    st.dataframe(pending, width="stretch", hide_index=True)


def _bekleyen_listeyi_cek(engine, u_rol, u_dept_id):
    """ONAY BEKLIYOR durumundaki kayıtları çeker."""
    params, where = {}, "WHERE vp.onay_durumu = 'ONAY BEKLIYOR'"
    if u_dept_id and u_rol != "ADMIN":
        ids = get_all_sub_department_ids(u_dept_id)
        where += " AND p.qms_departman_id IN :dept_ids"
        params["dept_ids"] = tuple(ids)
    sql = f"""
        SELECT vp.id, p.ad_soyad, d.ad as bolum,
               vp.baslangic_tarihi, vp.bitis_tarihi,
               vp.vardiya, vp.izin_gunleri, vp.plan_tipi, vp.onay_durumu
        FROM personel_vardiya_programi vp
        JOIN ayarlar_kullanicilar p ON vp.personel_id = p.id
        LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id
        {where}
        ORDER BY vp.baslangic_tarihi DESC
    """
    with engine.connect() as conn:
        res = conn.execute(text(sql), params)
        return pd.DataFrame(res.fetchall(), columns=res.keys())


def _onayli_rapor_sql(u_rol, u_dept):
    """Onaylı vardiya raporu SQL'ini ve parametrelerini hazırlar."""
    params, where = {}, "WHERE vp.onay_durumu = 'ONAYLANDI'"
    if u_dept and u_rol != "ADMIN":
        if isinstance(u_dept, list):
            where += " AND p.qms_departman_id IN :dept_ids"
            params["dept_ids"] = tuple(u_dept)
        else:
            where += " AND p.qms_departman_id = :dept_id"
            params["dept_id"] = u_dept
    sql = f"""
        SELECT p.ad_soyad as "Personel", p.gorev as "Görev",
               d.ad as "Bölüm", p.servis_duragi as "🚌 Servis Güzergahı",
               vp.baslangic_tarihi as "Başlangıç", vp.bitis_tarihi as "Bitiş",
               vp.vardiya as "Vardiya", vp.izin_gunleri as "İzin BM",
               vp.plan_tipi as "Plan Tipi", vp.onay_durumu as "Durum"
        FROM personel_vardiya_programi vp
        JOIN ayarlar_kullanicilar p ON vp.personel_id = p.id
        LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id
        {where}
        ORDER BY vp.baslangic_tarihi DESC
    """
    return sql, params


def _render_shift_report(engine, u_rol, u_dept):
    """Onaylı vardiya raporu (servis detaylı)."""
    st.subheader("📊 Vardiya ve Servis Raporu")
    sql, params = _onayli_rapor_sql(u_rol, u_dept)
    with engine.connect() as conn:
        res = conn.execute(text(sql), params)
        df = pd.DataFrame(res.fetchall(), columns=res.keys())
    if "İzin BM" in df.columns:
        df["İzin Günleri"] = df["İzin BM"].apply(izin_str)
        df = df.drop(columns=["İzin BM"])
    st.dataframe(df, width="stretch", hide_index=True)
    if not df.empty:
        st.download_button(
            "📥 Excel Olarak İndir",
            df.to_csv(index=False).encode('utf-8'),
            "vardiya_ve_servis_raporu.csv", "text/csv"
        )
