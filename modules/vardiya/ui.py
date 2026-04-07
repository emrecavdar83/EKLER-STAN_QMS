import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from modules.vardiya.logic import (
    get_personnel_for_shift_management, get_active_shifts,
    save_shift_plan, approve_shifts
)
from logic.data_fetcher import run_query
from logic.auth_logic import kullanici_yetkisi_var_mi, normalize_role_string

def render_vardiya_module(engine):
    st.title("📅 Operasyonel Vardiya Yönetimi")
    st.info("Bölüm sorumluları kendi departmanları için haftalık/aylık vardiya planlaması yapabilir.")
    
    # 1. Yetki ve Filtreleme
    u_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper().strip()
    u_dept = st.session_state.get('user_dept_id', None)
    
    tabs = st.tabs(["✍️ Vardiya Yaz", "🚦 Onay Bekleyenler", "📊 Vardiya Raporu (Servis Detaylı)"])
    
    with tabs[0]:
        _render_shift_entry(engine, u_rol, u_dept)
        
    with tabs[1]:
        _render_approval_queue(engine, u_rol)
        
    with tabs[2]:
        _render_shift_report(engine, u_rol, u_dept)

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
        st.warning("Bu bölüme ait aktif personel bulunamadı.")
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
        use_container_width=True,
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
        
    sql = """
        SELECT vp.id, p.ad_soyad, p.bolum, vp.baslangic_tarihi, vp.bitis_tarihi, vp.vardiya, vp.onay_durumu
        FROM personel_vardiya_programi vp
        JOIN personel p ON vp.personel_id = p.id
        WHERE vp.onay_durumu = 'ONAY BEKLIYOR'
        ORDER BY vp.baslangic_tarihi DESC
    """
    pending_df = run_query(sql)
    
    if pending_df.empty:
        st.info("Şu anda onay bekleyen bir plan bulunmuyor.")
        return
        
    selected_ids = st.multiselect("Onaylanacak Kayıtları Seçiniz", pending_df['id'].tolist(), format_func=lambda x: f"ID: {x}")
    
    c1, c2 = st.columns(2)
    if c1.button("✅ Seçilenleri Onayla", use_container_width=True):
        if selected_ids:
            success, msg = approve_shifts(engine, selected_ids, st.session_state.get('user_id', 0))
            if success: st.success(msg); st.rerun()
            else: st.error(msg)
    
    st.dataframe(pending_df, use_container_width=True, hide_index=True)

def _render_shift_report(engine, u_rol, u_dept):
    st.subheader("📊 Vardiya ve Servis Raporu")
    
    # v8.3: Servis güzergahı raporun kalbinde
    rep_sql = """
        SELECT 
            p.ad_soyad as "Personel",
            p.gorev as "Görev",
            p.bolum as "Bölüm",
            p.servis_duragi as "🚌 Servis Güzergahı",
            vp.baslangic_tarihi as "Başlangıç",
            vp.bitis_tarihi as "Bitiş",
            vp.vardiya as "Vardiya",
            vp.onay_durumu as "Durum"
        FROM personel_vardiya_programi vp
        JOIN personel p ON vp.personel_id = p.id
        WHERE vp.onay_durumu = 'ONAYLANDI'
        ORDER BY vp.baslangic_tarihi DESC
    """
    report_df = run_query(rep_sql)
    st.dataframe(report_df, use_container_width=True, hide_index=True)
    
    if not report_df.empty:
        st.download_button("📥 Excel Olarak İndir", report_df.to_csv(index=False).encode('utf-8'), "vardiya_ve_servis_raporu.csv", "text/csv")
