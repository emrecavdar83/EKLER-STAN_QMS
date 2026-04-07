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
    st.subheader("🏭 QMS Departman Hiyerarşisi & Matrix Yönetimi")
    st.info("Bu bölüm BRC/IFS standartlarına göre organize edilmiştir. 20 katman derinlik ve Matrix (Çoklu Bağlılık) desteği aktiftir.")

    from logic.data_fetcher import get_qms_department_tree, get_qms_department_options_hierarchical, run_query
    
    # 1. Ağaç Görünümü (Salt Okunur / Hızlı)
    with st.expander("🌳 Organizasyon Şeması Görünümü", expanded=True):
        tree = get_qms_department_tree()
        if tree:
            for item in tree:
                st.markdown(f"• {item}")
        else:
            st.warning("Henüz departman tanımlanmamış.")

    # 2. Departman Yönetim Editörü
    st.divider()
    st.markdown("### 📝 Departman & Matrix Düzenle")
    dept_df = run_query("SELECT id, ad, ust_id, ikincil_ust_id, tur_id, yonetici_id, kod, dil_anahtari, sira_no, aktif FROM qms_departmanlar ORDER BY sira_no")
    
    # Yardımcı Veriler
    type_df = run_query("SELECT id, tur_adi FROM qms_departman_turleri")
    type_map = dict(zip(type_df['id'], type_df['tur_adi']))
    type_names = list(type_map.values())

    dept_options = get_qms_department_options_hierarchical()
    dept_names = list(dept_options.values())

    pers_df = run_query("SELECT id, ad_soyad FROM personel WHERE aktif = 1 ORDER BY ad_soyad")
    pers_map = {0: "- Atanmamış -"}
    for _, r in pers_df.iterrows(): pers_map[r['id']] = r['ad_soyad']
    pers_names = list(pers_map.values())

    # Mapping for display
    dept_df['ust_ad'] = dept_df['ust_id'].fillna(0).astype(int).map(dept_options).fillna("- Kök -")
    dept_df['ikincil_ust_ad'] = dept_df['ikincil_ust_id'].fillna(0).astype(int).map(dept_options).fillna("- Yok -")
    dept_df['tur_ad'] = dept_df['tur_id'].fillna(0).astype(int).map(type_map).fillna("-")
    dept_df['yonetici_adi'] = dept_df['yonetici_id'].fillna(0).astype(int).map(pers_map).fillna("-")

    edited_df = st.data_editor(
        dept_df, use_container_width=True, hide_index=True,
        column_config={
            "id": None, "ust_id": None, "tur_id": None, "ikincil_ust_id": None, "yonetici_id": None,
            "ad": st.column_config.TextColumn("🏠 Birim Adı", width="large", required=True),
            "kod": st.column_config.TextColumn("🆔 Kod (XX-YY)", width="small"),
            "ust_ad": st.column_config.SelectboxColumn("📂 Ana Üst Birim", options=dept_names),
            "ikincil_ust_ad": st.column_config.SelectboxColumn("🔗 Matrix (2. Üst)", options=dept_names),
            "tur_ad": st.column_config.SelectboxColumn("🏷️ Tür", options=type_names),
            "yonetici_adi": st.column_config.SelectboxColumn("👤 Sorumlu", options=pers_names),
            "dil_anahtari": st.column_config.TextColumn("🌐 Dil Key"),
            "sira_no": st.column_config.NumberColumn("🔢 Sıra", min_value=0),
            "aktif": st.column_config.CheckboxColumn("✅ Aktif")
        }
    )

    if st.button("💾 Departman & Matrix Değişikliklerini Kaydet", use_container_width=True, type="primary"):
        try:
            name_to_dept_id = {v: k for k, v in dept_options.items()}
            name_to_type_id = {v: k for k, v in type_map.items()}
            name_to_pers_id = {v: k for k, v in pers_map.items()}

            with engine.begin() as conn:
                for _, row in edited_df.iterrows():
                    u_id = name_to_dept_id.get(row['ust_ad'])
                    i_u_id = name_to_dept_id.get(row['ikincil_ust_ad'])
                    t_id = name_to_type_id.get(row['tur_ad'])
                    y_id = name_to_pers_id.get(row['yonetici_adi'])
                    
                    sql = text("""
                        UPDATE qms_departmanlar 
                        SET ad=:ad, kod=:kod, ust_id=:u, ikincil_ust_id=:iu, tur_id=:t, yonetici_id=:y, dil_anahtari=:l, sira_no=:s, aktif=:act, guncelleme_tarihi=CURRENT_TIMESTAMP 
                        WHERE id=:id
                    """)
                    conn.execute(sql, {
                        "ad": str(row['ad']).upper(), "kod": row['kod'],
                        "u": u_id if u_id and u_id > 0 else None,
                        "iu": i_u_id if i_u_id and i_u_id > 0 else None,
                        "t": t_id, "y": y_id if y_id and y_id > 0 else None,
                        "l": row['dil_anahtari'], "s": row['sira_no'], 
                        "act": 1 if row['aktif'] else 0, "id": row['id']
                    })
            
            clear_department_cache()
            st.success("✅ Organizasyon şeması ve Matrix bağları güncellendi!")
            time.sleep(0.5); st.rerun()
        except Exception as e:
            st.error(f"❌ Kayıt hatası: {e}")
    render_sync_button(key_prefix="bolumler_ui")
