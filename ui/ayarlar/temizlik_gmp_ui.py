import streamlit as st
import pandas as pd
from sqlalchemy import text
import time

from logic.data_fetcher import (
    veri_getir
)
from logic.cache_manager import clear_personnel_cache
from logic.settings_logic import find_excel_column
from logic.sync_handler import render_sync_button

def render_temizlik_tab(engine):
    st.subheader("🧹 Master Temizlik Planı ve Tanımları")
    t_plan, t_metot, t_kimyasal, t_val = st.tabs(["📅 Master Temizlik Planı", "📝 Metotlar", "🧪 Kimyasallar", "✅ Doğrulama Kriterleri"])
    
    with t_plan:
        st.caption("Master Temizlik Planı Yönetimi")
        try:
            # Metot listesini selectbox için çek
            df_met_opts = pd.read_sql("SELECT id, metot_adi FROM tanim_metotlar", engine)
            met_mapping = {row['id']: row['metot_adi'] for _, row in df_met_opts.iterrows()}
            met_list = ["- Seçiniz -"] + list(met_mapping.values())
            met_reverse_mapping = {v: k for k, v in met_mapping.items()}

            plan_df = pd.read_sql("SELECT id, * FROM ayarlar_temizlik_plani", engine)
            
            # Görüntüleme için metot ismini ekle
            plan_df['metot_adi_display'] = plan_df['metot_id'].map(met_mapping).fillna("- Seçiniz -")
            
            ed_plan = st.data_editor(
                plan_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "id": None,
                    "metot_id": None,
                    "metot_adi_display": st.column_config.SelectboxColumn("📝 Temizlik Metodu", options=met_list, required=True),
                    "yuzey_tipi": st.column_config.TextColumn("🧱 Yüzey Tipi", placeholder="Örn: Paslanmaz"),
                    "kat": st.column_config.TextColumn("🏢 Kat"),
                    "kat_bolum": st.column_config.TextColumn("🏭 Bölüm"),
                    "yer_ekipman": st.column_config.TextColumn("⚙️ Ekipman/Alan"),
                    "kimyasal": st.column_config.TextColumn("🧪 Kimyasal")
                }
            )

            if st.button("💾 Plan Değişikliklerini Kaydet"):
                with engine.begin() as conn:
                    for _, row in ed_plan.iterrows():
                        r_dict = row.to_dict()
                        # Metot ID'sini eşle
                        m_name = r_dict.get('metot_adi_display')
                        r_dict['metot_id'] = met_reverse_mapping.get(m_name)
                        
                        # Gereksiz sütunları temizle
                        r_dict.pop('metot_adi_display', None)
                        row_id = r_dict.pop('id', None)
                        
                        # NaN temizliği
                        for k, v in r_dict.items():
                            if pd.isna(v): r_dict[k] = None

                        if row_id:
                            # Mevcut kaydı güncelle
                            sql = "UPDATE ayarlar_temizlik_plani SET " + ", ".join([f"{k}=:{k}" for k in r_dict.keys()]) + " WHERE id=:rid"
                            r_dict['rid'] = row_id
                            conn.execute(text(sql), r_dict)
                        else:
                            # Yeni kayıt (id SERIAL/AUTOINCREMENT tarafından üretilecek)
                            cols = ", ".join(r_dict.keys())
                            vals = ", ".join([f":{k}" for k in r_dict.keys()])
                            conn.execute(text(f"INSERT INTO ayarlar_temizlik_plani ({cols}) VALUES ({vals})"), r_dict)
                st.success("Plan başarıyla güncellendi!"); time.sleep(0.5); st.rerun()

        except Exception as e: 
            st.info(f"Plan yüklenemedi: {e}")

        if st.button("🗑️ TÜM PLANI SIFIRLA", type="secondary"):
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS ayarlar_temizlik_plani"))
                conn.commit()
            st.warning("Temizlendi."); time.sleep(0.5); st.rerun()

    with t_metot:
        try:
            df_met = veri_getir("Tanim_Metotlar")
            ed_met = st.data_editor(df_met, num_rows="dynamic", use_container_width=True, key="ed_met_ui")
            if st.button("💾 Metotları Kaydet"):
                with engine.begin() as conn:
                    for _, row in ed_met.iterrows():
                        conn.execute(text("""
                            INSERT INTO tanim_metotlar (metot_adi, aciklama)
                            VALUES (:metot_adi, :aciklama)
                            ON CONFLICT(metot_adi) DO UPDATE SET
                                aciklama = excluded.aciklama
                        """), row.to_dict())
                st.success("Kaydedildi!"); time.sleep(0.5); st.rerun()
        except: st.info("Metot Listesi Alınamadı")

    with t_kimyasal:
        try:
            df_kim = veri_getir("Kimyasal_Envanter")
            ed_kim = st.data_editor(df_kim, num_rows="dynamic", use_container_width=True, key="ed_kim_ui")
            if st.button("💾 Kimyasalları Kaydet"):
                with engine.begin() as conn:
                    for _, row in ed_kim.iterrows():
                        # NaN/None kontrolü ve temizliği (to_sql otomatik yapıyordu)
                        r_dict = row.to_dict()
                        for k, v in r_dict.items():
                            if pd.isna(v): r_dict[k] = None
                        
                        conn.execute(text("""
                            INSERT INTO kimyasal_envanter (kimyasal_adi, tedarikci, msds_yolu, tds_yolu)
                            VALUES (:kimyasal_adi, :tedarikci, :msds_yolu, :tds_yolu)
                            ON CONFLICT(kimyasal_adi) DO UPDATE SET
                                tedarikci = excluded.tedarikci,
                                msds_yolu = excluded.msds_yolu,
                                tds_yolu = excluded.tds_yolu
                        """), r_dict)
                st.success("Kaydedildi!"); time.sleep(0.5); st.rerun()
        except: st.info("Kimyasal Listesi Alınamadı")

    with t_val:
        st.caption("Metot Bazlı Doğrulama ve Validasyon Kriterleri")
        _temizlik_validasyon_ekle(engine)
        st.divider()
        _temizlik_validasyon_duzenle(engine)
        st.divider()
        _temizlik_validasyon_listesi(engine)
    
    render_sync_button(key_prefix="temizlik_ui")

def render_gmp_soru_tab(engine):
    st.subheader("🛡️ GMP Denetimi - Soru Bankası Yönetimi")
    t1, t2 = st.tabs(["📋 Mevcut Sorular", "➕ Yeni Soru Ekle"])
    
    with t1:
        try:
            qs_df = veri_getir("GMP_Soru_Havuzu")
            ed_qs = st.data_editor(qs_df, num_rows="dynamic", use_container_width=True, key="ed_gmp_qs_ui")
            if st.button("💾 GMP Sorularını Güncelle"):
                with engine.connect() as conn:
                    conn.execute(text("DELETE FROM gmp_soru_havuzu"))
                    ed_qs.to_sql("gmp_soru_havuzu", engine, if_exists='append', index=False)
                    conn.commit()
                st.success("Güncellendi!"); time.sleep(0.5); st.rerun()
        except: st.info("Soru Havuzu Alınamadı")

    with t2:
        with st.form("new_gmp_q_ui"):
            q_kat = st.selectbox("Kategori", ["Hijyen", "Operasyon", "Bina/Altyapı", "Genel"])
            q_txt = st.text_area("Soru Metni")
            q_risk = st.selectbox("Risk", [1,2,3])
            if st.form_submit_button("Soru Kaydet") and q_txt:
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO gmp_soru_havuzu (kategori, soru_metni, risk_puani) VALUES (:k, :s, :r)"), {"k":q_kat, "s":q_txt, "r":q_risk})
                    conn.commit()
                st.success("Eklendi!"); time.sleep(0.5); st.rerun()

    render_sync_button(key_prefix="gmp_soru_ui")

# --- DOĞRULAMA KRİTERLERİ HELPERS ---

def _temizlik_validasyon_listesi(engine):
    """Mevcut kriterleri tablo olarak gösterir."""
    query = """
        SELECT 
            v.id,
            m.metot_adi,
            v.yuzey_tipi,
            v.min_konsantrasyon,
            v.max_konsantrasyon,
            v.min_sicaklik,
            v.max_sicaklik,
            v.temas_suresi_dk,
            v.rlu_esik_degeri,
            v.notlar
        FROM temizlik_dogrulama_kriterleri v
        JOIN tanim_metotlar m ON v.metot_id = m.id
        WHERE v.aktif = 1
    """
    try:
        df = pd.read_sql(query, engine)
        if not df.empty:
            st.write("**Mevcut Kriterler Listesi**")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Henüz tanımlanmış doğrulama kriteri bulunmuyor.")
    except Exception as e:
        st.error(f"Liste yüklenirken hata: {e}")

def _temizlik_validasyon_ekle(engine):
    """Yeni kriter ekleme formu."""
    with st.expander("➕ Yeni Doğrulama Kriteri Ekle"):
        try:
            metotlar = pd.read_sql("SELECT id, metot_adi FROM tanim_metotlar", engine)
            if metotlar.empty:
                st.warning("Önce metot tanımlamalısınız.")
                return
            
            with st.form("new_validation_criteria_form"):
                col1, col2 = st.columns(2)
                m_id = col1.selectbox("Metot", metotlar['id'], format_func=lambda x: metotlar[metotlar['id']==x]['metot_adi'].iloc[0])
                y_tipi = col2.text_input("Yüzey Tipi", placeholder="Örn: Paslanmaz, Plastik")
                
                c1, c2 = st.columns(2)
                min_k = c1.number_input("Min Konsantrasyon (%)", value=0.0, step=0.1)
                max_k = c2.number_input("Max Konsantrasyon (%)", value=0.0, step=0.1)
                
                s1, s2 = st.columns(2)
                min_s = s1.number_input("Min Sıcaklık (°C)", value=0.0, step=1.0)
                max_s = s2.number_input("Max Sıcaklık (°C)", value=0.0, step=1.0)
                
                t1, r1 = st.columns(2)
                t_sure = t1.number_input("Temas Süresi (Dk)", value=0, step=1)
                rlu = r1.number_input("RLU Eşik Değeri", value=0.0, step=10.0)
                
                note = st.text_area("Uygulama Notları")
                
                if st.form_submit_button("💾 Kriteri Kaydet"):
                    if not y_tipi:
                        st.error("Yüzey tipi boş olamaz.")
                        return
                    
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO temizlik_dogrulama_kriterleri 
                            (metot_id, yuzey_tipi, min_konsantrasyon, max_konsantrasyon, min_sicaklik, max_sicaklik, temas_suresi_dk, rlu_esik_degeri, notlar)
                            VALUES (:m_id, :y_tipi, :min_k, :max_k, :min_s, :max_s, :t_sure, :rlu, :note)
                            ON CONFLICT(metot_id, yuzey_tipi) DO UPDATE SET
                                min_konsantrasyon = excluded.min_konsantrasyon,
                                max_konsantrasyon = excluded.max_konsantrasyon,
                                min_sicaklik = excluded.min_sicaklik,
                                max_sicaklik = excluded.max_sicaklik,
                                temas_suresi_dk = excluded.temas_suresi_dk,
                                rlu_esik_degeri = excluded.rlu_esik_degeri,
                                notlar = excluded.notlar,
                                aktif = 1
                        """), {
                            "m_id": m_id, "y_tipi": y_tipi, "min_k": min_k, "max_k": max_k, 
                            "min_s": min_s, "max_s": max_s, "t_sure": t_sure, "rlu": rlu, "note": note
                        })
                    st.success("Kriter başarıyla kaydedildi/güncellendi!")
                    time.sleep(0.5); st.rerun()
        except Exception as e:
            st.error(f"Form yüklenirken hata: {e}")

def _temizlik_validasyon_duzenle(engine):
    """Mevcut kriterleri st.data_editor ile düzenle."""
    try:
        df = pd.read_sql("SELECT * FROM temizlik_dogrulama_kriterleri WHERE aktif = 1", engine)
        if not df.empty:
            st.write("**📝 Kriterleri Hızlı Düzenle**")
            # Sadece sayısal ve not sütunlarını düzenlenebilir kılalım, metot_id ve yuzey_tipi index gibi kalsın (veya UPSERT için gerekli)
            ed_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="ed_val_criteria", disabled=["id", "metot_id", "yuzey_tipi"])
            
            if st.button("💾 Değişiklikleri Uygula"):
                with engine.begin() as conn:
                    for _, row in ed_df.iterrows():
                        r_dict = row.to_dict()
                        # NaN temizliği
                        for k, v in r_dict.items():
                            if pd.isna(v): r_dict[k] = None
                        
                        conn.execute(text("""
                            INSERT INTO temizlik_dogrulama_kriterleri 
                            (metot_id, yuzey_tipi, min_konsantrasyon, max_konsantrasyon, min_sicaklik, max_sicaklik, temas_suresi_dk, rlu_esik_degeri, notlar, aktif)
                            VALUES (:metot_id, :yuzey_tipi, :min_konsantrasyon, :max_konsantrasyon, :min_sicaklik, :max_sicaklik, :temas_suresi_dk, :rlu_esik_degeri, :notlar, :aktif)
                            ON CONFLICT(metot_id, yuzey_tipi) DO UPDATE SET
                                min_konsantrasyon = excluded.min_konsantrasyon,
                                max_konsantrasyon = excluded.max_konsantrasyon,
                                min_sicaklik = excluded.min_sicaklik,
                                max_sicaklik = excluded.max_sicaklik,
                                temas_suresi_dk = excluded.temas_suresi_dk,
                                rlu_esik_degeri = excluded.rlu_esik_degeri,
                                notlar = excluded.notlar,
                                aktif = excluded.aktif
                        """), r_dict)
                st.success("Tüm değişiklikler kaydedildi!")
                time.sleep(0.5); st.rerun()
    except Exception as e:
        st.info("Kriter düzenleme alanı yüklenemedi.")
