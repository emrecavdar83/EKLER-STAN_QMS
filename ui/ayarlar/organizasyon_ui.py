import streamlit as st
import pandas as pd
from sqlalchemy import text
import time

from logic.data_fetcher import (
    get_department_tree, get_department_options_hierarchical
)
from logic.cache_manager import clear_personnel_cache, clear_department_cache
from logic.sync_handler import render_sync_button

def render_rol_tab(engine):
    st.subheader("🎭 Rol Yönetimi")
    with st.expander("➕ Yeni Rol Ekle"):
        with st.form("new_role_form_ui"):
            new_rol_adi = st.text_input("Rol Adı")
            new_rol_aciklama = st.text_area("Açıklama")
            if st.form_submit_button("Rolü Ekle"):
                if new_rol_adi:
                    try:
                        # --- ANAYASA v4.0: ATOMIK TRANSACTION ---
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO ayarlar_roller (rol_adi, aciklama) VALUES (:r, :a)"), {"r": new_rol_adi, "a": new_rol_aciklama})
                        st.toast("✅ Yeni rol başarıyla eklendi!"); time.sleep(0.5); st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Rol ekleme hatası: {e}")

    from logic.data_fetcher import run_query
    roller_df = run_query("SELECT * FROM ayarlar_roller ORDER BY id")
    edited_roller = st.data_editor(roller_df, use_container_width=True, hide_index=True, num_rows="dynamic", key="editor_roller_ui")
    if st.button("💾 Rolleri Kaydet"):
        try:
            with engine.begin() as conn:
                for _, row in edited_roller.iterrows():
                    # Cast boolean to int systematically (Anayasa v3.2)
                    is_active = 1 if row['aktif'] in [True, 1, 'True', '1'] else 0
                    if pd.notna(row['id']):
                        conn.execute(text("UPDATE ayarlar_roller SET rol_adi=:r, aciklama=:a, aktif=:act WHERE id=:id"), 
                                     {"r":row['rol_adi'], "a":row['aciklama'], "act":is_active, "id":row['id']})
                    else:
                        conn.execute(text("INSERT INTO ayarlar_roller (rol_adi, aciklama, aktif) VALUES (:r, :a, :act)"), 
                                     {"r":row['rol_adi'], "a":row['aciklama'], "act":is_active})
            clear_personnel_cache(); st.toast("✅ Rol listesi güncellendi!"); time.sleep(0.5); st.rerun()
        except Exception as e:
            st.error(f"⚠️ Rol kayıt hatası: {e}")
    render_sync_button(key_prefix="roller_ui")

def render_yetki_tab(engine):
    st.subheader("🔑 Zone & Modül Yetki Matrisi")
    from logic.data_fetcher import run_query
    roller_df = run_query("SELECT rol_adi, aktif FROM ayarlar_roller")
    if not roller_df.empty:
        roller_aktif = roller_df[roller_df['aktif'].isin([True, 1, 'true', '1', 'True'])]
        secili_rol = st.selectbox("🎭 Rol Seçin", roller_aktif['rol_adi'].tolist(), key="select_rol_yetki_ui")
        
        # v4.0: HİBRİT ZONE SEÇİMİ (EKL-ZONE-GRID)
        zone_labels = {"ops": "🏭 Operasyon (ops)", "mgt": "📊 Yönetim (mgt)", "sys": "⚙️ Sistem (sys)"}
        secili_zone_anahtar = st.radio("📍 Zone Seçin", options=["ops", "mgt", "sys"], 
                                      format_func=lambda x: zone_labels[x], horizontal=True)
        
        from logic.auth_logic import sistem_modullerini_ve_anahtarlarini_getir
        modul_dict = sistem_modullerini_ve_anahtarlarini_getir() # {Etiket: Anahtar}
        
        # Modüllerin zone bilgilerini çek
        modul_info_df = run_query("SELECT modul_anahtari, zone FROM ayarlar_moduller")
        modul_to_zone = dict(zip(modul_info_df['modul_anahtari'], modul_info_df['zone']))
        
        mevcut_yetkiler = run_query("SELECT modul_adi, erisim_turu FROM ayarlar_yetkiler WHERE rol_adi = :r", params={"r": secili_rol})
        
        yetki_data = []
        for m_etiket, m_anahtar in modul_dict.items():
            # Sadece seçili Zone'a ait modülleri göster
            if modul_to_zone.get(m_anahtar) == secili_zone_anahtar:
                matches = mevcut_yetkiler[mevcut_yetkiler['modul_adi'] == m_anahtar]
                yetki = matches.iloc[0]['erisim_turu'] if not matches.empty else "Yok"
                yetki_data.append({"Modül": m_etiket, "Anahtar": m_anahtar, "Yetki": yetki})

        if not yetki_data:
            st.warning(f"Bu bölgede ({zone_labels[secili_zone_anahtar]}) tanımlı modül bulunamadı.")
            return

        df_yetki = pd.DataFrame(yetki_data)
        edited_yetkiler = st.data_editor(df_yetki, use_container_width=True, hide_index=True, key=f"editor_yetki_ui_{secili_rol}_{secili_zone_anahtar}", 
            column_config={
                "Anahtar": None,
                "Modül": st.column_config.TextColumn("Modül", disabled=True),
                "Yetki": st.column_config.SelectboxColumn("Yetki", options=["Yok", "Görüntüle", "Düzenle"])
            })

        if st.button(f"💾 {secili_rol} - {zone_labels[secili_zone_anahtar]} Yetkilerini Kaydet"):
            try:
                with engine.begin() as conn:
                    # SADECE SEÇİLİ ZONE'A AİT olanları sil ve tekrar ekle (Atomic Zone Update)
                    target_keys = df_yetki['Anahtar'].tolist()
                    if target_keys:
                        placeholders = ", ".join([f":m{i}" for i in range(len(target_keys))])
                        p_dict = {f"m{i}": k for i, k in enumerate(target_keys)}
                        p_dict['r'] = secili_rol
                        conn.execute(text(f"DELETE FROM ayarlar_yetkiler WHERE rol_adi = :r AND modul_adi IN ({placeholders})"), p_dict)
                    
                    for _, row in edited_yetkiler.iterrows():
                        conn.execute(text("INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (:r, :m, :e)"), 
                                     {"r": secili_rol, "m": row['Anahtar'], "e": row['Yetki']})
                
                # Cache temizliği
                from logic.zone_yetki import yetki_haritasi_yukle
                yetki_haritasi_yukle(engine, secili_rol, force_refresh=True)
                st.toast(f"✅ {secili_rol} yetkileri ({secili_zone_anahtar}) güncellendi!"); time.sleep(0.5); st.rerun()
            except Exception as e:
                st.error(f"⚠️ Yetki güncelleme hatası: {e}")
                

    render_sync_button(key_prefix="yetki_ui")

def render_bolum_tab(engine):
    st.subheader("🏭 Departman Yönetimi")
    
    def display_tree_local(df, parent_id=None, level=0):
        children = df[df['ana_departman_id'].fillna(0) == (parent_id if parent_id else 0)]
        for _, row in children.iterrows():
            indent = "&nbsp;" * (level * 8)
            st.markdown(f"{indent}🏢 **{row['bolum_adi']}** (ID: {row['id']})")
            display_tree_local(df, row['id'], level + 1)

    from logic.data_fetcher import run_query
    bolumler_df = run_query("SELECT * FROM ayarlar_bolumler ORDER BY sira_no")
    dept_options = get_department_options_hierarchical()

    with st.expander("➕ Yeni Departman Ekle"):
        with st.form("new_bolum_form_ui"):
            n_adi = st.text_input("Adı")
            p_opts = {0: "- Yok -"}; p_opts.update(dept_options)
            n_parent = st.selectbox("Bağlı Olduğu", options=list(p_opts.keys()), format_func=lambda x: p_opts[x])
            if st.form_submit_button("Ekle") and n_adi:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO ayarlar_bolumler (bolum_adi, ana_departman_id, aktif, sira_no) VALUES (:b, :p, 1, 10)"), 
                                   {"b": n_adi.upper(), "p": None if n_parent == 0 else n_parent})
                        try:
                            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('DEPARTMAN_EKLE', :d)"), {"d": f"{n_adi.upper()} eklendi."})
                        except: pass
                    clear_department_cache(); st.toast("✅ Departman başarıyla eklendi!"); time.sleep(0.5); st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Ekleme başarısız: {e}")

    if not bolumler_df.empty:
        display_tree_local(bolumler_df)
        edited_bolumler = st.data_editor(bolumler_df, use_container_width=True, hide_index=True, key="editor_bolumler_ui")
        if st.button("💾 Departmanları Kaydet"):
            try:
                with engine.begin() as conn:
                    for _, row in edited_bolumler.iterrows():
                        # Cast boolean to int systematically (Anayasa v3.2)
                        is_active = 1 if row['aktif'] in [True, 1, 'True', '1'] else 0
                        if pd.notna(row['id']):
                            conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi=:b, ana_departman_id=:p, aktif=:act, sira_no=:s WHERE id=:id"),
                                       {"b":row['bolum_adi'], "p":None if pd.isna(row['ana_departman_id']) or row['ana_departman_id']==0 else row['ana_departman_id'], 
                                        "act":is_active, "s":row['sira_no'], "id":row['id']})
                    try:
                        conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('DEPARTMAN_GUNCELLE', 'Departman listesi güncellendi.')"))
                    except: pass
                clear_personnel_cache(); st.toast("✅ Departman listesi güncellendi!"); time.sleep(0.5); st.rerun()
            except Exception as e:
                st.error(f"⚠️ Güncelleme başarısız: {e}")
    render_sync_button(key_prefix="bolumler_ui")
