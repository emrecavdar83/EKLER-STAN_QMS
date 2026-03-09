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
                    with engine.connect() as conn:
                        conn.execute(text("INSERT INTO ayarlar_roller (rol_adi, aciklama) VALUES (:r, :a)"), {"r": new_rol_adi, "a": new_rol_aciklama})
                        conn.commit()
                    st.success(f"✅ eklendi!"); time.sleep(1); st.rerun()

    from logic.data_fetcher import run_query
    roller_df = run_query("SELECT * FROM ayarlar_roller ORDER BY id")
    edited_roller = st.data_editor(roller_df, use_container_width=True, hide_index=True, num_rows="dynamic", key="editor_roller_ui")
    if st.button("💾 Rolleri Kaydet"):
        with engine.connect() as conn:
            for _, row in edited_roller.iterrows():
                if pd.notna(row['id']):
                    conn.execute(text("UPDATE ayarlar_roller SET rol_adi=:r, aciklama=:a, aktif=:act WHERE id=:id"), {"r":row['rol_adi'], "a":row['aciklama'], "act":row['aktif'], "id":row['id']})
                else:
                    conn.execute(text("INSERT INTO ayarlar_roller (rol_adi, aciklama, aktif) VALUES (:r, :a, :act)"), {"r":row['rol_adi'], "a":row['aciklama'], "act":row['aktif']})
            conn.commit()
        clear_personnel_cache(); st.success("✅ Güncellendi!"); time.sleep(1); st.rerun()
    render_sync_button(key_prefix="roller_ui")

def render_yetki_tab(engine):
    st.subheader("🔑 Yetki Matrisi")
    from logic.data_fetcher import run_query
    roller_df = run_query("SELECT rol_adi, aktif FROM ayarlar_roller")
    if not roller_df.empty:
        # Cross-DB güvenliği için (SQLite'da 1, Postgres'te True gelebilir) Python tarafında filtreleme
        roller_aktif = roller_df[roller_df['aktif'].isin([True, 1, 'true', '1', 'True'])]
        secili_rol = st.selectbox("Rol Seçin", roller_aktif['rol_adi'].tolist(), key="select_rol_yetki_ui")
        
        from logic.auth_logic import sistem_modullerini_ve_anahtarlarini_getir
        modul_dict = sistem_modullerini_ve_anahtarlarini_getir()
        
        mevcut_yetkiler = run_query("SELECT modul_adi, erisim_turu FROM ayarlar_yetkiler WHERE rol_adi = :r", params={"r": secili_rol})
        
        yetki_data = []
        for m_etiket, m_anahtar in modul_dict.items():
            matches = mevcut_yetkiler[mevcut_yetkiler['modul_adi'] == m_anahtar]
            if not matches.empty:
                yetki = matches.iloc[0]['erisim_turu']
            else:
                # Geriye dönük uyumluluk: eski etiket veritabanında var mı?
                 # (Örn: 'Üretim Girişi' -> KeyError, bu yüzden str(m_etiket) içinde arıyoruz)
                matches_eski = mevcut_yetkiler[mevcut_yetkiler['modul_adi'].isin([m_etiket, m_etiket.replace('🏭 ', ''), m_etiket.split(' ', 1)[-1]])]
                if not matches_eski.empty:
                    yetki = matches_eski.iloc[0]['erisim_turu']
                else:
                    yetki = "Yok"
            yetki_data.append({"Modül": m_etiket, "Anahtar": m_anahtar, "Yetki": yetki})

        df_yetki = pd.DataFrame(yetki_data)
        
        edited_yetkiler = st.data_editor(df_yetki, use_container_width=True, hide_index=True, key=f"editor_yetki_ui_{secili_rol}", 
            column_config={
                "Anahtar": None, # Kullanıcıdan gizle (arka planda key olarak kalır)
                "Modül": st.column_config.TextColumn("Modül", disabled=True),
                "Yetki": st.column_config.SelectboxColumn("Yetki", options=["Yok", "Görüntüle", "Düzenle"])
            })

        if st.button(f"💾 {secili_rol} Yetkilerini Kaydet"):
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM ayarlar_yetkiler WHERE rol_adi = :r"), {"r": secili_rol})
                for _, row in edited_yetkiler.iterrows():
                    # Her durumda Anayasa kurallarına uygun olarak ANAHTAR kaydedilecek.
                    conn.execute(text("INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (:r, :m, :e)"), 
                                 {"r": secili_rol, "m": row['Anahtar'], "e": row['Yetki']})
                conn.commit()
            st.success("✅ Güncellendi!"); time.sleep(1); st.rerun()
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
                    with engine.connect() as conn:
                        conn.execute(text("INSERT INTO ayarlar_bolumler (bolum_adi, ana_departman_id, aktif, sira_no) VALUES (:b, :p, TRUE, 10)"), 
                                   {"b": n_adi.upper(), "p": None if n_parent == 0 else n_parent})
                        try:
                            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('DEPARTMAN_EKLE', :d)"), {"d": f"{n_adi.upper()} eklendi."})
                        except: pass
                        conn.commit()
                    clear_department_cache(); st.success("✅ Eklendi!"); time.sleep(1); st.rerun()
                except Exception as e:
                    st.error("Ekleme başarısız: Veritabanı hatası")

    if not bolumler_df.empty:
        display_tree_local(bolumler_df)
        edited_bolumler = st.data_editor(bolumler_df, use_container_width=True, hide_index=True, key="editor_bolumler_ui")
        if st.button("💾 Departmanları Kaydet"):
            try:
                with engine.connect() as conn:
                    for _, row in edited_bolumler.iterrows():
                        if pd.notna(row['id']):
                            conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi=:b, ana_departman_id=:p, aktif=:act, sira_no=:s WHERE id=:id"),
                                       {"b":row['bolum_adi'], "p":None if pd.isna(row['ana_departman_id']) or row['ana_departman_id']==0 else row['ana_departman_id'], 
                                        "act":row['aktif'], "s":row['sira_no'], "id":row['id']})
                    try:
                        conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('DEPARTMAN_GUNCELLE', 'Departman listesi güncellendi.')"))
                    except: pass
                    conn.commit()
                clear_personnel_cache(); st.success("✅ Güncellendi!"); time.sleep(1); st.rerun()
            except Exception as e:
                st.error("Güncelleme başarısız: Veritabanı hatası")
    render_sync_button(key_prefix="bolumler_ui")
