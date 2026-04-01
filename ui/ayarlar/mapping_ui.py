import streamlit as st
import pandas as pd
from sqlalchemy import text
import time
from logic.data_fetcher import run_query, get_qms_department_options_hierarchical
from logic.cache_manager import clear_personnel_cache

def render_mapping_tab(engine):
    st.subheader("🔗 Personel Departman Eşleştirme (Migration)")
    st.info("Eski sistemdeki metin bazlı bölüm isimlerini, yeni hiyerarşik QMS departmanları ile eşleştirin.")

    # 1. Bekleyen Personel Listesi
    try:
        sql = """
            SELECT id, ad_soyad, bolum as eski_bolum, qms_departman_id 
            FROM personel 
            WHERE (qms_departman_id IS NULL OR qms_departman_id = 0)
            AND (durum = 'AKTİF' OR durum IS NULL)
            ORDER BY bolum, ad_soyad
        """
        pending_df = run_query(sql)
        
        if pending_df.empty:
            st.success("✅ Tüm personeller yeni hiyerarşik yapıya başarıyla eşleştirilmiş!")
            if st.button("Tüm Personel Listesini Gör"):
                full_sql = "SELECT id, ad_soyad, bolum as eski_bolum, qms_departman_id FROM personel WHERE durum = 'AKTİF' OR durum IS NULL"
                st.dataframe(run_query(full_sql), use_container_width=True)
            return

        st.warning(f"⚠️ Toplam {len(pending_df)} personel eşleştirme bekliyor.")

        # 2. Toplu Eşleştirme (Smart Suggester)
        with st.expander("🪄 Akıllı Toplu Eşleştirme (Advanced)", expanded=False):
            unique_old = pending_df['eski_bolum'].unique()
            dept_options = get_qms_department_options_hierarchical()
            
            c1, c2 = st.columns(2)
            old_name = c1.selectbox("Eski Bölüm Adı", unique_old)
            new_id = c2.selectbox("Yeni QMS Departmanı", options=list(dept_options.keys()), format_func=lambda x: dept_options[x])
            
            if st.button(f"'{old_name}' olan tüm personelleri eşleştir", type="primary"):
                try:
                    with engine.begin() as conn:
                        conn.execute(text("UPDATE personel SET qms_departman_id = :nid WHERE bolum = :oname AND (durum = 'AKTİF' OR durum IS NULL)"), 
                                     {"nid": new_id, "oname": old_name})
                    st.success(f"✅ {old_name} bölümündeki personeller aktarıldı!"); time.sleep(0.5); st.rerun()
                except Exception as e:
                    st.error(f"Toplu eşleştirme hatası: {e}")

        # 3. Manuel Eşleştirme Editörü
        st.write("---")
        st.markdown("### 📋 Bireysel Eşleştirme Listesi")
        
        # Display Mapping
        dept_options = get_qms_department_options_hierarchical()
        dept_names = list(dept_options.values())
        
        pending_df['yeni_departman'] = pending_df['qms_departman_id'].fillna(0).astype(int).map(dept_options).fillna("- Seçiniz -")
        
        edited_df = st.data_editor(
            pending_df, use_container_width=True, hide_index=True,
            column_config={
                "id": None, "qms_departman_id": None,
                "ad_soyad": st.column_config.TextColumn("👤 Personel Adı", disabled=True),
                "eski_bolum": st.column_config.TextColumn("📂 Eski Bölüm (Metin)", disabled=True),
                "yeni_departman": st.column_config.SelectboxColumn("🏗️ Yeni QMS Hiyerarşisi", options=dept_names, required=True)
            }
        )

        if st.button("💾 Seçili Eşleştirmeleri Kaydet", use_container_width=True):
            try:
                name_to_id = {v: k for k, v in dept_options.items()}
                with engine.begin() as conn:
                    for _, row in edited_df.iterrows():
                        target_id = name_to_id.get(row['yeni_departman'])
                        if target_id and target_id > 0:
                            conn.execute(text("UPDATE personel SET qms_departman_id = :nid WHERE id = :pid"), 
                                         {"nid": target_id, "pid": row['id']})
                
                clear_personnel_cache()
                st.success("✅ Eşleştirmeler kaydedildi!"); time.sleep(0.5); st.rerun()
            except Exception as e:
                st.error(f"Kayıt hatası: {e}")

    except Exception as e:
        st.error(f"Eşleştirme yükleme hatası: {e}")
