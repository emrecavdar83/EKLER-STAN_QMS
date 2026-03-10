# ui/ayarlar/flow_designer_ui.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
import time
from logic.data_fetcher import run_query

def render_flow_designer(engine):
    st.subheader("🕸️ Akıllı Akış Tasarımcısı (Smart Flow)")
    tab1, tab2, tab3 = st.tabs(["📁 Akış Tanımları", "📍 Düğüm (Node) Yönetimi", "🔗 Bağlantı (Edge) Editörü"])

    # --- TAB 1: Akış Tanımları ---
    with tab1:
        st.caption("Ürün gruplarına özel ana akış rotalarını buradan tanımlayın.")
        flows = pd.read_sql("SELECT * FROM flow_definitions ORDER BY id", engine)
        
        with st.expander("➕ Yeni Akış Ekle"):
            f_name = st.text_input("Akış Adı (Örn: Ekler Hattı)")
            f_urun = st.text_input("Ürün Grubu (Örn: Ekler)")
            if st.button("💾 Akışı Kaydet") and f_name:
                with engine.begin() as conn:
                    conn.execute(text("INSERT INTO flow_definitions (flow_name, urun_grubu) VALUES (:n, :u)"), {"n": f_name, "u": f_urun})
                st.success("Akış eklendi!"); time.sleep(1); st.rerun()
        
        st.dataframe(flows, use_container_width=True, hide_index=True)

    # --- TAB 2: Düğüm (Node) Yönetimi ---
    with tab2:
        if flows.empty:
            st.warning("Önce bir akış tanımlamalısınız.")
        else:
            selected_flow_id = st.selectbox("Akış Seçiniz", flows['id'], format_func=lambda x: flows[flows['id']==x]['flow_name'].iloc[0])
            nodes = pd.read_sql(text("SELECT * FROM flow_nodes WHERE flow_id = :fid ORDER BY sira_no"), engine, params={"fid": selected_flow_id})
            
            with st.expander("➕ Yeni Düğüm Ekle"):
                col1, col2 = st.columns(2)
                n_name = col1.text_input("Düğüm Adı (Örn: Pişirme)")
                n_type = col2.selectbox("Düğüm Tipi", ["GİRİŞ", "PROSES", "ÖLÇÜM", "KARAR", "ÇIKIŞ"])
                n_sira = col1.number_input("Sıra No", value=10, step=10)
                
                # Lokasyon seçimi
                loks = pd.read_sql("SELECT id, ad, tip FROM lokasyonlar WHERE aktif = 1", engine)
                n_lok = col2.selectbox("Lokasyon (Ekipman/Bölüm)", loks['id'], format_func=lambda x: f"{loks[loks['id']==x]['ad'].iloc[0]} ({loks[loks['id']==x]['tip'].iloc[0]})")
                
                if st.button("💾 Düğümü Ekle") and n_name:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO flow_nodes (flow_id, node_name, node_type, lokasyon_id, sira_no) VALUES (:fid, :n, :t, :l, :s)"),
                                     {"fid": selected_flow_id, "n": n_name, "t": n_type, "l": n_lok, "s": n_sira})
                    st.success("Düğüm eklendi!"); time.sleep(1); st.rerun()
            
            st.dataframe(nodes, use_container_width=True, hide_index=True)

    # --- TAB 3: Bağlantı (Edge) Editörü ---
    with tab3:
        if flows.empty:
            st.warning("Önce bir akış tanımlamalısınız.")
        else:
            sel_flow_id = st.selectbox("Bağlantı İçin Akış Seçiniz", flows['id'], format_func=lambda x: flows[flows['id']==x]['flow_name'].iloc[0], key="edge_flow_sel")
            current_nodes = pd.read_sql(text("SELECT id, node_name FROM flow_nodes WHERE flow_id = :fid"), engine, params={"fid": sel_flow_id})
            edges = pd.read_sql(text("SELECT * FROM flow_edges WHERE flow_id = :fid"), engine, params={"fid": sel_flow_id})

            if current_nodes.empty:
                st.info("Bu akışta henüz düğüm yok.")
            else:
                with st.expander("🔗 Yeni Bağlantı Ekle"):
                    c1, c2 = st.columns(2)
                    source = c1.selectbox("Kaynak Düğüm", current_nodes['id'], format_func=lambda x: current_nodes[current_nodes['id']==x]['node_name'].iloc[0])
                    target = c2.selectbox("Hedef Düğüm", current_nodes['id'], format_func=lambda x: current_nodes[current_nodes['id']==x]['node_name'].iloc[0])
                    cond = st.text_input("Koşul (Opsiyonel - örn: Ürün=Ekler)")
                    
                    if st.button("➕ Bağlantıyı Kur"):
                        if source == target:
                            st.error("Kaynak ve hedef aynı olamaz.")
                        else:
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO flow_edges (flow_id, source_node_id, target_node_id, condition_rule) VALUES (:fid, :s, :t, :c)"),
                                             {"fid": sel_flow_id, "s": source, "t": target, "c": cond})
                            st.success("Bağlantı kuruldu!"); time.sleep(1); st.rerun()
                
                st.dataframe(edges, use_container_width=True, hide_index=True)
