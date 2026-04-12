import streamlit as st
import pandas as pd
from sqlalchemy import text
import time

from logic.data_fetcher import (
    get_hierarchy_flat
)
from logic.cache_manager import clear_personnel_cache
from logic.sync_handler import render_sync_button

def _get_lokasyon_tipleri(engine):
    """DB'den tipleri çeker. Hata olursa Anayasa gereği fallback listesine döner."""
    try:
        t_df = pd.read_sql("SELECT tip_adi FROM lokasyon_tipleri WHERE aktif = 1 ORDER BY sira_no", engine)
        if not t_df.empty:
            return t_df['tip_adi'].tolist()
    except Exception:
        pass
    return ["Kat", "Bölüm", "Hat", "Ekipman"]

def _render_lokasyon_form(engine, lok_df, lst_bolumler, lok_tipleri):
    """Yeni Lokasyon Ekleme Formu"""
    with st.expander("➕ Yeni Lokasyon Ekle"):
        col1, col2 = st.columns(2)
        new_lok_tip = col1.selectbox("Lokasyon Tipi", lok_tipleri, key="new_lok_tip_ui")
        new_lok_ad = col2.text_input("Lokasyon Adı", key="new_lok_ad_ui")
        new_lok_dept = col1.selectbox("Sorumlu Departman", ["(Seçiniz)"] + lst_bolumler, key="new_lok_dept_ui")

        parent_options = {0: "- Ana Lokasyon -"}
        if not lok_df.empty:
            parents = pd.DataFrame()
            # Dinamik fallback eşleşmeleri (Strict hardcode'dan kaçınmak için genel tip eşleşmesi)
            idx = lok_tipleri.index(new_lok_tip) if new_lok_tip in lok_tipleri else -1
            if idx > 0:
                parents = lok_df[lok_df['tip'] == lok_tipleri[idx-1]]
            elif idx == 0:
                parents = pd.DataFrame() # Kat ise parent yok
            else:
                parents = lok_df # Fallback
            
            for _, row in parents.iterrows():
                icon = '🏢' if row['tip']=='Kat' else '🏭' if row['tip']=='Bölüm' else '🛤️' if row['tip']=='Hat' else '⚙️'
                parent_options[row['id']] = f"{icon} {row['ad']}"

        new_parent = st.selectbox("Üst Lokasyon", options=list(parent_options.keys()), format_func=lambda x: parent_options[x], key="new_parent_ui")

        if st.button("💾 Lokasyonu Ekle", use_container_width=True):
            if new_lok_ad:
                try:
                    # --- ANAYASA v4.0: ATOMIK TRANSACTION ---
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO lokasyonlar (ad, tip, parent_id, sorumlu_departman) VALUES (:a, :t, :p, :d)"),
                                   {"a": new_lok_ad, "t": new_lok_tip, "p": None if new_parent == 0 else new_parent, "d": new_lok_dept if new_lok_dept != "(Seçiniz)" else None})
                        
                        # Madde 6: Audit Log Zırhı (Artık aynı transaksiyonun parçası)
                        try:
                            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('LOKASYON_EKLE', :d)"), {"d": f"{new_lok_ad} ({new_lok_tip}) eklendi."})
                        except: pass
                        
                    clear_personnel_cache(); st.toast("✅ Fabrika Lokasyonu başarıyla eklendi!"); time.sleep(0.5); st.rerun()
                except Exception as e:
                    from logic.error_handler import handle_exception
                    handle_exception(e, modul="FABRIKA_UI", user_msg="Lokasyon eklenirken bir sorun oluştu.")

def _render_lokasyon_table(engine, lok_df):
    """Lokasyonları Düzenleme ve Ağaç Gösterimi"""
    if not lok_df.empty:
        st.caption("📋 Mevcut Lokasyon Hiyerarşisi")
        for _, kat in lok_df[lok_df['tip'] == 'Kat'].iterrows():
            with st.container(border=True):
                st.markdown(f"🏢 **{kat['ad']}**")
                bolumler = lok_df[(lok_df['tip'] == 'Bölüm') & (lok_df['parent_id'] == kat['id'])]
                for _, bolum in bolumler.iterrows():
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🏭 **{bolum['ad']}**")

        with st.expander("📝 Lokasyonları Düzenle"):
            edited_lok = st.data_editor(lok_df, use_container_width=True, hide_index=True, key="editor_lokasyonlar_ui")
            if st.button("💾 Lokasyonları Kaydet"):
                try:
                    with engine.begin() as conn:
                        for _, row in edited_lok.iterrows():
                            # Cast boolean to int systematically (Anayasa v3.2)
                            is_active = 1 if row['aktif'] in [True, 1, 'True', '1'] else 0
                            conn.execute(text("UPDATE lokasyonlar SET ad=:ad, tip=:tip, parent_id=:pid, sorumlu_departman=:sdep, aktif=:aktif, sira_no=:sira WHERE id=:id"),
                                       {"ad":row['ad'], "tip":row['tip'], "pid":None if pd.isna(row['parent_id']) or row['parent_id']==0 else row['parent_id'], 
                                        "sdep":row['sorumlu_departman'], "aktif":is_active, "sira":row['sira_no'], "id":row['id']})
                        
                        try:
                            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('LOKASYON_GUNCELLE', 'Lokasyonlar toplu güncellendi.')"))
                        except: pass
                        
                    clear_personnel_cache(); st.toast("✅ Lokasyon hiyerarşisi başarıyla güncellendi!"); time.sleep(0.5); st.rerun()
                except Exception as e:
                    from logic.error_handler import handle_exception
                    handle_exception(e, modul="FABRIKA_UI", user_msg="Lokasyon güncellenirken bir sorun oluştu.")

def render_lokasyon_tab(engine):
    st.subheader("📍 Lokasyon Yönetimi (Hiyerarşik)")
    st.caption("Fabrika lokasyon hiyerarşisini ve sorumlu departmanları buradan yönetebilirsiniz")

    lst_bolumler = []
    try:
        b_df = pd.read_sql("SELECT id, ad as bolum_adi, ust_id as ana_departman_id, aktif FROM qms_departmanlar WHERE aktif = 1", engine)
        lst_bolumler = get_hierarchy_flat(b_df)
    except:
        lst_bolumler = ["Üretim", "Depo", "Kalite", "Bakım"]

    try:
        lok_df = pd.read_sql("SELECT * FROM lokasyonlar ORDER BY tip, sira_no, ad", engine)
    except:
        lok_df = pd.DataFrame()

    lok_tipleri = _get_lokasyon_tipleri(engine)

    try:
        _render_lokasyon_form(engine, lok_df, lst_bolumler, lok_tipleri)
    except Exception as e:
        st.error("Lokasyon ekleme formunda beklenmeyen bir hata oluştu.")
        
    try:
        _render_lokasyon_table(engine, lok_df)
    except Exception as e:
        st.error("Lokasyon tablosunda beklenmeyen bir hata oluştu.")
        
    render_sync_button(key_prefix="lokasyonlar_ui")

def render_proses_tab(engine):
    st.subheader("🔧 Modüler Proses Yönetimi")
    t_proses1, t_proses2 = st.tabs(["📋 Proses Tipleri", "🔗 Lokasyon-Proses Ataması"])
    with t_proses1:
        proses_df = pd.read_sql("SELECT * FROM proses_tipleri ORDER BY id", engine)
        with st.expander("➕ Yeni Proses Tipi Ekle"):
            with st.form("new_proses_form_ui"):
                p_kod = st.text_input("Kod").upper()
                p_ad = st.text_input("Ad")
                if st.form_submit_button("Ekle") and p_kod and p_ad:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO proses_tipleri (kod, ad) VALUES (:k, :a)"), {"k": p_kod, "a": p_ad})
                        clear_personnel_cache(); st.toast("✅ Proses Tipi Eklendi!"); time.sleep(0.5); st.rerun()
                    except Exception as e:
                        from logic.error_handler import handle_exception
                        handle_exception(e, modul="FABRIKA_UI", user_msg="Proses tipi eklenirken bir sorun oluştu.")
        st.dataframe(proses_df, use_container_width=True, hide_index=True)
    render_sync_button(key_prefix="proses_ui")
