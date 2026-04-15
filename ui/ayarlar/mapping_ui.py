import streamlit as st
import pandas as pd
from sqlalchemy import text
from logic.data_fetcher import run_query, get_qms_department_options_hierarchical
from logic.cache_manager import clear_personnel_cache

def _render_bulk_mapping(engine, pending_df, dept_options):
    """Toplu eşleştirme arayüzünü yönetir."""
    with st.expander("🪄 Akıllı Toplu Eşleştirme (Advanced)", expanded=False):
        unique_old = pending_df['eski_bolum'].unique()
        c1, c2 = st.columns(2)
        old_name = c1.selectbox("Eski Bölüm Adı", unique_old)
        new_id = c2.selectbox("Yeni QMS Departmanı", options=list(dept_options.keys()), format_func=lambda x: dept_options[x], key="bulk_qms_dept")
        
        if st.button(f"'{old_name}' olan tüm personelleri eşleştir", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(text("UPDATE personel SET qms_departman_id = :nid WHERE bolum = :oname AND (durum = 'AKTİF' OR durum IS NULL)"), 
                                 {"nid": new_id, "oname": old_name})
                st.success(f"✅ {old_name} bölümündeki personeller aktarıldı!"); st.rerun()
            except Exception as e:
                st.error(f"Toplu eşleştirme hatası: {e}")

def _render_individual_mapping(engine, edited_df, dept_options):
    """Bireysel eşleştirme kayıt işlemini yönetir."""
    if st.button("💾 Seçili Eşleştirmeleri Kaydet", width="stretch"):
        try:
            name_to_id = {v: k for k, v in dept_options.items()}
            with engine.begin() as conn:
                for _, row in edited_df.iterrows():
                    target_id = name_to_id.get(row['yeni_departman'])
                    if target_id and target_id > 0:
                        conn.execute(text("UPDATE personel SET qms_departman_id = :nid WHERE id = :pid"), 
                                     {"nid": target_id, "pid": row['id']})
            
            clear_personnel_cache()
            st.success("✅ Eşleştirmeler kaydedildi!"); st.rerun()
        except Exception as e:
            st.error(f"Kayıt hatası: {e}")

def render_mapping_tab(engine):
    """v6.1.0: Refaktör edilmiş ana eşleştirme sekmesi."""
    st.subheader("🔗 Personel Departman Eşleştirme (Migration)")
    st.info("Eski sistemdeki metin bazlı bölüm isimlerini, yeni hiyerarşik QMS departmanları ile eşleştirin.")

    try:
        sql = "SELECT id, ad_soyad, bolum as eski_bolum, qms_departman_id FROM personel WHERE (qms_departman_id IS NULL OR qms_departman_id = 0) AND (durum = 'AKTİF' OR durum IS NULL) ORDER BY bolum, ad_soyad"
        pending_df = run_query(sql)
        
        if pending_df.empty:
            st.success("✅ Tüm personeller yeni hiyerarşik yapıya başarıyla eşleştirilmiş!")
            return

        dept_options = get_qms_department_options_hierarchical()
        _render_bulk_mapping(engine, pending_df, dept_options)
        
        st.write("---")
        st.markdown("### 📋 Bireysel Eşleştirme Listesi")
        
        pending_df['yeni_departman'] = pending_df['qms_departman_id'].fillna(0).astype(int).map(dept_options).fillna("- Seçiniz -")
        
        edited_df = st.data_editor(
            pending_df, width="stretch", hide_index=True,
            column_config={
                "id": None, "qms_departman_id": None,
                "ad_soyad": st.column_config.TextColumn("👤 Personel Adı", disabled=True),
                "eski_bolum": st.column_config.TextColumn("📂 Eski Bölüm (Metin)", disabled=True),
                "yeni_departman": st.column_config.SelectboxColumn("🏗️ Yeni QMS Hiyerarşisi", options=list(dept_options.values()), required=True)
            }
        )

        _render_individual_mapping(engine, edited_df, dept_options)

    except Exception as e:
        st.error(f"Eşleştirme yükleme hatası: {e}")
