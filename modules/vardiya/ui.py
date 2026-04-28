import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from modules.vardiya.logic import (
    get_personnel_for_shift_management, get_active_shifts,
    save_shift_plan, approve_shifts
)
from logic.data_fetcher import run_query, get_department_options_hierarchical, get_all_sub_department_ids
from logic.auth_logic import kullanici_yetkisi_var_mi, normalize_role_string
from sqlalchemy import text

def render_vardiya_module(engine):
    st.title("📅 Operasyonel Vardiya Yönetimi")
    st.info("Bölüm sorumluları kendi departmanları için haftalık/aylık vardiya planlaması yapabilir.")
    
    # 1. Yetki ve Filtreleme
    u_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper().strip()
    u_dept_id = st.session_state.get('user_dept_id', None)
    
    # v6.3.5: Robust Hierarchical Filter UI
    dept_options = get_department_options_hierarchical()
    active_filter_ids = None

    # Seçenek B: Tüm kullanıcılar bölüm süzebilsin (Kolaylık için)
    default_index = 0
    if u_dept_id and u_dept_id in dept_options:
        default_index = list(dept_options.keys()).index(u_dept_id)

    selected_dept_id = st.selectbox("🏢 Bölüm Seçiniz (Filtrelemek için)", 
                                    options=list(dept_options.keys()), 
                                    format_func=lambda x: dept_options.get(x), 
                                    index=default_index, key="vardiya_dept_filter")
    if selected_dept_id > 0:
        active_filter_ids = get_all_sub_department_ids(selected_dept_id)

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

def _render_shift_entry(engine, u_rol, u_dept):
    st.subheader("✍️ Personel Vardiya Girişi (Toplu)")
    
    # Filtreleme
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Başlangıç Tarihi", datetime.now())
    with c2:
        end_date = st.date_input("Bitiş Tarihi", datetime.now() + timedelta(days=6))
        
    # Personel Verisi
    p_df = get_personnel_for_shift_management(engine, dept_id=u_dept, user_rol=u_rol)
    
    if p_df.empty:
        st.warning("Bu bölüme ait aktif ayarlar_kullanicilar bulunamadı.")
        return
        
    # Aktif Vardiyalar (v8.3: Dinamik 6+ Vardiya)
    v_df = get_active_shifts(engine)
    v_names = v_df['tip_adi'].tolist() if not v_df.empty else ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI", "OFF"]
    if "OFF" not in v_names: v_names.append("OFF")
    
    # Editor
    st.write(f"📊 Toplam {len(p_df)} Personel için Planlama")
    
    # Vardiya ve İzin Giriş Alanı (v8.3: Servis Detaylı)
    p_df['vardiya'] = v_names[0]
    p_df['izin_gunleri'] = ""
    p_df['aciklama'] = ""
    
    edited_df = st.data_editor(
        p_df,
        column_config={
            "id": None,
            "ad_soyad": st.column_config.TextColumn("Personel", disabled=True, width="medium"),
            "gorev": st.column_config.TextColumn("Görev", disabled=True),
            "servis_duragi": st.column_config.TextColumn("🚌 Servis", disabled=True),
            "vardiya": st.column_config.SelectboxColumn("⏰ Vardiya", options=v_names, required=True),
            "izin_gunleri": st.column_config.TextColumn("📅 Haftalık İzin(ler)", help="Örn: Pazartesi, Salı"),
            "aciklama": st.column_config.TextColumn("💬 Notlar")
        },
        width="stretch",
        hide_index=True
    )
    
    if st.button("🚀 Onaya Gönder"):
        records = []
        for _, row in edited_df.iterrows():
            records.append({
                "personel_id": row['id'],
                "baslangic_tarihi": str(start_date),
                "bitis_tarihi": str(end_date),
                "vardiya": row['vardiya'],
                "izin_gunleri": row['izin_gunleri'],
                "aciklama": row['aciklama'],
                "durum": "ONAY BEKLIYOR" # v8.3: Onay Akışı
            })
        
        success, msg = save_shift_plan(engine, records, st.session_state.get('user_id', 0))
        if success:
            st.success("Vardiya planı amir onayına gönderildi!"); st.rerun()
        else:
            st.error(f"Hata: {msg}")

def _render_approval_queue(engine, u_rol):
    st.subheader("🚦 Onay Bekleyen Vardiya Planları")
    # v8.3: Sadece amirler görebilir (ADMIN, MÜDÜR, ŞEF)
    if not (u_rol in ['ADMIN', 'MÜDÜR', 'KOORDİNATÖR / ŞEF']):
        st.warning("Bu alanı sadece onay yetkisi olan amirler görebilir.")
        return
        
    u_dept_id = st.session_state.get('user_dept_id', None)
    params = {}
    where_clause = "WHERE vp.onay_durumu = 'ONAY BEKLIYOR'"
    
    if u_dept_id and u_rol != "ADMIN":
        allowed_ids = get_all_sub_department_ids(u_dept_id)
        where_clause += " AND p.qms_departman_id IN :dept_ids"
        params["dept_ids"] = tuple(allowed_ids)

    sql = f"""
        SELECT vp.id, p.ad_soyad, d.ad as bolum, vp.baslangic_tarihi, vp.bitis_tarihi, vp.vardiya, vp.onay_durumu
        FROM personel_vardiya_programi vp
        JOIN ayarlar_kullanicilar p ON vp.personel_id = p.id
        LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id
        {where_clause}
        ORDER BY vp.baslangic_tarihi DESC
    """
    
    with engine.connect() as conn:
        res = conn.execute(text(sql), params)
        pending_df = pd.DataFrame(res.fetchall(), columns=res.keys())
    
    if pending_df.empty:
        st.info("Şu anda onay bekleyen bir plan bulunmuyor.")
        return
        
    selected_ids = st.multiselect("Onaylanacak Kayıtları Seçiniz", pending_df['id'].tolist(), format_func=lambda x: f"ID: {x}")
    
    c1, c2 = st.columns(2)
    if c1.button("✅ Seçilenleri Onayla", width="stretch"):
        if selected_ids:
            success, msg = approve_shifts(engine, selected_ids, st.session_state.get('user_id', 0))
            if success: st.success(msg); st.rerun()
            else: st.error(msg)
    
    st.dataframe(pending_df, width="stretch", hide_index=True)

def _render_shift_report(engine, u_rol, u_dept):
    st.subheader("📊 Vardiya ve Servis Raporu")
    
    params = {}
    where_clause = "WHERE vp.onay_durumu = 'ONAYLANDI'"
    
    if u_dept and u_rol != "ADMIN":
        if isinstance(u_dept, list):
            where_clause += " AND p.qms_departman_id IN :dept_ids"
            params["dept_ids"] = tuple(u_dept)
        else:
            where_clause += " AND p.qms_departman_id = :dept_id"
            params["dept_id"] = u_dept

    # v8.3.1: Servis güzergahı raporun kalbinde (QMS Integrated)
    rep_sql = f"""
        SELECT 
            p.ad_soyad as "Personel",
            p.gorev as "Görev",
            d.ad as "Bölüm",
            p.servis_duragi as "🚌 Servis Güzergahı",
            vp.baslangic_tarihi as "Başlangıç",
            vp.bitis_tarihi as "Bitiş",
            vp.vardiya as "Vardiya",
            vp.onay_durumu as "Durum"
        FROM personel_vardiya_programi vp
        JOIN ayarlar_kullanicilar p ON vp.personel_id = p.id
        LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id
        {where_clause}
        ORDER BY vp.baslangic_tarihi DESC
    """
    
    with engine.connect() as conn:
        res = conn.execute(text(rep_sql), params)
        report_df = pd.DataFrame(res.fetchall(), columns=res.keys())
        
    st.dataframe(report_df, width="stretch", hide_index=True)
    
    if not report_df.empty:
        st.download_button("📥 Excel Olarak İndir", report_df.to_csv(index=False).encode('utf-8'), "vardiya_ve_servis_raporu.csv", "text/csv")
