import streamlit as st
import pandas as pd
from sqlalchemy import text
import time

from logic.data_fetcher import (
    get_hierarchy_flat
)
from logic.cache_manager import clear_personnel_cache
from logic.sync_handler import render_sync_button

def render_lokasyon_tab(engine):
    st.subheader("📍 Lokasyon Yönetimi (Kat > Bölüm > Hat > Ekipman)")
    st.caption("Fabrika lokasyon hiyerarşisini ve sorumlu departmanları buradan yönetebilirsiniz")

    lst_bolumler = []
    try:
        b_df = pd.read_sql("SELECT * FROM ayarlar_bolumler WHERE aktif IS TRUE", engine)
        lst_bolumler = get_hierarchy_flat(b_df)
    except:
        lst_bolumler = ["Üretim", "Depo", "Kalite", "Bakım"]

    try:
        lok_df = pd.read_sql("SELECT * FROM lokasyonlar ORDER BY tip, sira_no, ad", engine)
    except:
        lok_df = pd.DataFrame()

    with st.expander("➕ Yeni Lokasyon Ekle"):
        col1, col2 = st.columns(2)
        new_lok_tip = col1.selectbox("Lokasyon Tipi", ["Kat", "Bölüm", "Hat", "Ekipman"], key="new_lok_tip_ui")
        new_lok_ad = col2.text_input("Lokasyon Adı", key="new_lok_ad_ui")
        new_lok_dept = col1.selectbox("Sorumlu Departman", ["(Seçiniz)"] + lst_bolumler, key="new_lok_dept_ui")

        parent_options = {0: "- Ana Lokasyon -"}
        if not lok_df.empty:
            parents = pd.DataFrame()
            if new_lok_tip == "Bölüm": parents = lok_df[lok_df['tip'] == 'Kat']
            elif new_lok_tip == "Hat": parents = lok_df[lok_df['tip'] == 'Bölüm']
            elif new_lok_tip == "Ekipman": parents = lok_df[lok_df['tip'].isin(['Kat', 'Bölüm', 'Hat'])]
            
            for _, row in parents.iterrows():
                icon = '🏢' if row['tip']=='Kat' else '🏭' if row['tip']=='Bölüm' else '🛤️' if row['tip']=='Hat' else '⚙️'
                parent_options[row['id']] = f"{icon} {row['ad']}"

        new_parent = st.selectbox("Üst Lokasyon", options=list(parent_options.keys()), format_func=lambda x: parent_options[x], key="new_parent_ui")

        if st.button("💾 Lokasyonu Ekle", use_container_width=True):
            if new_lok_ad:
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO lokasyonlar (ad, tip, parent_id, sorumlu_departman) VALUES (:a, :t, :p, :d)"),
                               {"a": new_lok_ad, "t": new_lok_tip, "p": None if new_parent == 0 else new_parent, "d": new_lok_dept if new_lok_dept != "(Seçiniz)" else None})
                    conn.commit()
                clear_personnel_cache(); st.success(f"✅ Eklendi!"); time.sleep(1); st.rerun()

    if not lok_df.empty:
        # Ağaç Görünümü (Basitleştirildi)
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
                with engine.connect() as conn:
                    for _, row in edited_lok.iterrows():
                        conn.execute(text("UPDATE lokasyonlar SET ad=:ad, tip=:tip, parent_id=:pid, sorumlu_departman=:sdep, aktif=:aktif, sira_no=:sira WHERE id=:id"),
                                   {"ad":row['ad'], "tip":row['tip'], "pid":None if pd.isna(row['parent_id']) or row['parent_id']==0 else row['parent_id'], "sdep":row['sorumlu_departman'], "aktif":row['aktif'], "sira":row['sira_no'], "id":row['id']})
                    conn.commit()
                clear_personnel_cache(); st.success("✅ Güncellendi!"); time.sleep(1); st.rerun()
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
                    with engine.connect() as conn:
                        conn.execute(text("INSERT INTO proses_tipleri (kod, ad) VALUES (:k, :a)"), {"k": p_kod, "a": p_ad})
                        conn.commit()
                    clear_personnel_cache(); st.success("✅ Eklendi!"); time.sleep(1); st.rerun()
        st.dataframe(proses_df, use_container_width=True, hide_index=True)
    render_sync_button(key_prefix="proses_ui")
