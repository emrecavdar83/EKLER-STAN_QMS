import streamlit as st
import pandas as pd
from sqlalchemy import text
import time

from logic.data_fetcher import (
    veri_getir, get_department_tree
)
from logic.cache_manager import clear_personnel_cache
from logic.sync_handler import render_sync_button

def render_urun_tab(engine):
    st.subheader("📦 Ürün Tanımlama ve Dinamik Parametreler")
    edited_products = pd.DataFrame() 

    # 1. Ana Ürün Listesi
    st.caption("📋 Ürün Listesi ve Numune Adetleri")
    try:
        u_df = veri_getir("Ayarlar_Urunler")

        if 'sorumlu_departman' not in u_df.columns:
            u_df['sorumlu_departman'] = None
        
        u_df['sorumlu_departman'] = u_df['sorumlu_departman'].replace(['None', 'none', 'nan', ''], None)

        dept_list = ["Tümü"] + get_department_tree(filter_tur="ÜRETİM")
        sel_dept = st.selectbox("📌 Bölüm Filtrele (Hızlı Erişim)", dept_list, key="prod_dept_filter_ui")

        full_product_df = u_df.copy()
        if sel_dept != "Tümü":
            u_df = u_df[u_df['sorumlu_departman'] == sel_dept]

        edited_products = st.data_editor(
            u_df, num_rows="dynamic", width="stretch", key="editor_products_ui",
            column_config={
                "uretim_bolumu": None,
                "urun_adi": st.column_config.TextColumn("Ürün Adı", required=True),
                "sorumlu_departman": st.column_config.SelectboxColumn("Sorumlu Departman", options=dept_list[1:], width="medium"),
                "alerjen_bilgisi": st.column_config.TextColumn("⚠️ Alerjen Bilgisi", help="Örn: Süt, Yumurta, Gluten"),
                "depolama_sartlari": st.column_config.TextColumn("❄️ Depolama Şartları", help="Örn: +4 Derece, -18 Derece"),
                "ambalaj_tipi": st.column_config.TextColumn("📦 Ambalaj Tipi"),
                "hedef_kitle": st.column_config.TextColumn("👥 Hedef Kitle/Uyarı", help="Örn: Bebeklere uygun değildir"),
                "versiyon_no": st.column_config.NumberColumn("vNo", min_value=1, default=1, disabled=True),
                "raf_omru_gun": st.column_config.NumberColumn("Raf Ömrü (Gün)", min_value=1),
                "numune_sayisi": st.column_config.NumberColumn("Numune Sayısı", min_value=1, max_value=20, default=3),
                "gramaj": st.column_config.NumberColumn("Gramaj (g)")
            }
        )

        if st.button("💾 Ana Ürün Listesini Kaydet", width="stretch"):
            if 'sorumlu_departman' in edited_products.columns:
                edited_products['sorumlu_departman'] = edited_products['sorumlu_departman'].replace(['None', 'none', 'nan', ''], None)
            
            final_df = edited_products if sel_dept == "Tümü" else full_product_df # Basitleştirildi: Filtreli modda kaydetme logic'i app.py'de kompleksti
            # app.py'deki merge logic'ini uygulayalım
            if sel_dept != "Tümü":
                 full_product_df.set_index("urun_adi", inplace=True)
                 edited_products.set_index("urun_adi", inplace=True)
                 full_product_df.update(edited_products)
                 final_df = full_product_df.reset_index()

            # Anayasa Madde 6: to_sql(replace) yerine UPSERT
            with engine.begin() as conn:
                for _, row in final_df.iterrows():
                    # Null check for string cols
                    row_dict = row.to_dict()
                    for col in ['alerjen_bilgisi', 'depolama_sartlari', 'ambalaj_tipi', 'hedef_kitle']:
                        if col not in row_dict or pd.isna(row_dict.get(col)):
                            row_dict[col] = ''
                    if 'versiyon_no' not in row_dict or pd.isna(row_dict.get('versiyon_no')):
                        row_dict['versiyon_no'] = 1

                    conn.execute(text("""
                        INSERT INTO ayarlar_urunler (
                            urun_adi, raf_omru_gun, olcum1_ad, olcum1_min, olcum1_max,
                            olcum2_ad, olcum2_min, olcum2_max, olcum3_ad, olcum3_min,
                            olcum3_max, olcum_sikligi_dk, uretim_bolumu, numune_sayisi,
                            sorumlu_departman, alerjen_bilgisi, depolama_sartlari, 
                            ambalaj_tipi, hedef_kitle, versiyon_no
                        ) VALUES (
                            :urun_adi, :raf_omru_gun, :olcum1_ad, :olcum1_min, :olcum1_max,
                            :olcum2_ad, :olcum2_min, :olcum2_max, :olcum3_ad, :olcum3_min,
                            :olcum3_max, :olcum_sikligi_dk, :uretim_bolumu, :numune_sayisi,
                            :sorumlu_departman, :alerjen_bilgisi, :depolama_sartlari, 
                            :ambalaj_tipi, :hedef_kitle, :versiyon_no
                        ) ON CONFLICT(urun_adi) DO UPDATE SET
                            raf_omru_gun = excluded.raf_omru_gun,
                            olcum1_ad = excluded.olcum1_ad,
                            olcum1_min = excluded.olcum1_min,
                            olcum1_max = excluded.olcum1_max,
                            olcum2_ad = excluded.olcum2_ad,
                            olcum2_min = excluded.olcum2_min,
                            olcum2_max = excluded.olcum2_max,
                            olcum3_ad = excluded.olcum3_ad,
                            olcum3_min = excluded.olcum3_min,
                            olcum3_max = excluded.olcum3_max,
                            olcum_sikligi_dk = excluded.olcum_sikligi_dk,
                            uretim_bolumu = excluded.uretim_bolumu,
                            numune_sayisi = excluded.numune_sayisi,
                            sorumlu_departman = excluded.sorumlu_departman,
                            alerjen_bilgisi = excluded.alerjen_bilgisi,
                            depolama_sartlari = excluded.depolama_sartlari,
                            ambalaj_tipi = excluded.ambalaj_tipi,
                            hedef_kitle = excluded.hedef_kitle,
                            versiyon_no = COALESCE(ayarlar_urunler.versiyon_no, 0) + 1
                    """), row_dict)
            
            clear_personnel_cache()
            st.toast("✅ Ürün listesi güncellendi!"); st.rerun()

    except Exception as e: st.error(f"Ürün verisi hatası: {e}")

    st.divider()
    _render_parametre_yonetimi(engine, edited_products)
    render_sync_button(key_prefix="urunler_ui")

def _render_parametre_yonetimi(engine, edited_products):
    st.subheader("🧪 Ürün Parametreleri (Brix, pH, Sıcaklık vb.)")
    if not edited_products.empty and "urun_adi" in edited_products.columns:
        urun_listesi = edited_products["urun_adi"].dropna().unique().tolist()
        secilen_urun_param = st.selectbox("Parametrelerini Düzenlemek İçin Ürün Seçiniz:", urun_listesi)

        if secilen_urun_param:
            param_df = pd.read_sql(text("SELECT * FROM urun_parametreleri WHERE urun_adi = :u"), engine, params={"u": secilen_urun_param})
            if param_df.empty:
                param_df = pd.DataFrame({"urun_adi": [secilen_urun_param], "parametre_adi": [""], "min_deger": [0.0], "max_deger": [0.0], "birim": [""]})
            else:
                if 'birim' not in param_df.columns:
                    param_df['birim'] = ""

            edited_params = st.data_editor(
                param_df, num_rows="dynamic", width="stretch", key=f"editor_params_ui_{secilen_urun_param}",
                column_config={
                    "id": None, 
                    "urun_adi": None, 
                    "parametre_adi": st.column_config.TextColumn("Parametre Adı", required=True, help="Örn: Brix, pH, Sıcaklık"),
                    "min_deger": st.column_config.NumberColumn("Minimum Değer"),
                    "max_deger": st.column_config.NumberColumn("Maksimum Değer"),
                    "birim": st.column_config.SelectboxColumn("Birim", options=["", "%", "°C", "pH", "g", "ml", "L", "Adet", "Saniye", "Dakika"], help="Ölçü Birimi")
                }
            )

            if st.button(f"💾 {secilen_urun_param} Parametrelerini Kaydet"):
                edited_params["urun_adi"] = secilen_urun_param
                edited_params = edited_params[edited_params["parametre_adi"] != ""]
                
                if not edited_params.empty:
                    # Anayasa Madde 6 Uyumu: UPSERT
                    with engine.begin() as conn:
                        # Önce mevcut olmayanları sil (Opsiyonel: Eğer UI'da silme yapıldıysa)
                        # Ama UPSERT mantığında silme ayrı ele alınır.
                        # Mevcut kodda DELETE vardı, yerine silinecekleri tespit edip silebiliriz
                        # veya kullanıcının istediği gibi sadece UPSERT yapabiliriz.
                        # Burada basitleştirmek için sadece UPSERT yapıyoruz:
                        if "id" in edited_params.columns: 
                            edited_params = edited_params.drop(columns=["id"])
                        
                        for _, row in edited_params.iterrows():
                            # DataFrame'de null kalırsa handle et
                            p_row = row.to_dict()
                            if pd.isna(p_row.get('birim')):
                                p_row['birim'] = ""
                                
                            conn.execute(text("""
                                INSERT INTO urun_parametreleri (urun_adi, parametre_adi, min_deger, max_deger, birim)
                                VALUES (:urun_adi, :parametre_adi, :min_deger, :max_deger, :birim)
                                ON CONFLICT(urun_adi, parametre_adi) DO UPDATE SET
                                    min_deger = excluded.min_deger,
                                    max_deger = excluded.max_deger,
                                    birim = excluded.birim
                            """), p_row)
                clear_personnel_cache(); st.toast("✅ Kaydedildi!"); st.rerun()
