import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
import time

from logic.data_fetcher import (
    veri_getir, run_query, get_department_options_hierarchical,
    get_all_sub_department_ids, get_department_tree,
    robust_id_clean
)
from logic.settings_logic import suggest_username
from logic.cache_manager import clear_personnel_cache, clear_all_cache
from logic.sync_handler import render_sync_button
from constants import POSITION_LEVELS

def render_personnel_tabs(engine):
    """Ayarlar modülü altındaki Personel ve Kullanıcı sekmelerini render eder."""
    
    # Bu fonksiyon hem tab1 hem de tab2 içeriğini bir wrapper olarak sunabilir 
    # veya ayrı fonksiyonlarda çağrılabilir. 
    # app.py'deki st.tabs yapısına uygun olarak bölüyoruz.
    pass

def render_personel_tab(engine):
    st.subheader("👷 Fabrika Personel Listesi Yönetimi")

    # Alt sekmeler: Form ve Tablo
    p_tabs = ["📅 Vardiya Çalışma Programı", "📝 Personel Ekle/Düzenle", "📋 Tüm Personel Listesi"]

    if "nav_personel" not in st.session_state:
        st.session_state["nav_personel"] = p_tabs[0]

    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
    p_selected_tab = st.radio(
        "Personel Sekmesi",
        p_tabs,
        index=p_tabs.index(st.session_state["nav_personel"]) if st.session_state["nav_personel"] in p_tabs else 0,
        key="nav_personel_ui",
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("---")

    # --- ERKEN YÜKLEME: LİSTELERİ HAZIRLA ---
    try:
        dept_options = get_department_options_hierarchical()
    except:
        dept_options = {0: "- Seçiniz -"}

    try:
        yon_df = run_query("SELECT id, ad_soyad FROM personel WHERE ad_soyad IS NOT NULL AND pozisyon_seviye <= 5 ORDER BY ad_soyad")
        yonetici_options = {0: "- Yok -"}
        for _, row in yon_df.iterrows():
            yonetici_options[row['id']] = row['ad_soyad']
    except:
        yonetici_options = {0: "- Yok -"}

    # >>> SEKME: VARDIYA ÇALIŞMA PROGRAMI <<<
    if p_selected_tab == p_tabs[0]:
        _render_vardiya_programi(engine, dept_options)

    # >>> SEKME: PERSONEL EKLE/DÜZENLE <<<
    elif p_selected_tab == p_tabs[1]:
        _render_personel_form(engine, dept_options, yonetici_options)

    # >>> SEKME: TÜM PERSONEL LİSTESİ <<<
    elif p_selected_tab == p_tabs[2]:
        _render_personel_listesi(engine, dept_options, yonetici_options)

    st.divider()
    render_sync_button(key_prefix="personel_ui")

def _render_vardiya_programi(engine, dept_options):
    st.subheader("📅 Dönemsel Vardiya Planlama (Toplu Giriş)")
    st.caption("Bölüm seçerek o bölümdeki tüm personellerin vardiya ve izinlerini tek seferde planlayabilirsiniz.")

    # ADIM 1: FİLTRELEME & HAZIRLIK
    with st.container():
        c1, c2, c3 = st.columns([2, 1, 1])
        secilen_bolum_id = c1.selectbox(
            "📍 Bölüm Seçimi (Listelemek için zorunludur)",
            options=list(dept_options.keys()),
            format_func=lambda x: dept_options[x],
            index=0
        )

        today = datetime.now()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        next_sunday = next_monday + timedelta(days=6)

        p_start = c2.date_input("Bağlangıç Tarihi", value=next_monday, key="vs_start")
        p_end = c3.date_input("Bitiş Tarihi", value=next_sunday, key="vs_end")

    st.divider()

    # ADIM 2: TOPLU LİSTE EDİTÖRÜ
    if secilen_bolum_id != 0:
        try:
            target_dept_ids = get_all_sub_department_ids(secilen_bolum_id)
            
            if len(target_dept_ids) == 1:
                t_sql = text("SELECT id, ad_soyad, gorev FROM personel WHERE durum = 'AKTİF' AND departman_id = :d ORDER BY ad_soyad")
                params = {"d": target_dept_ids[0]}
            else:
                ids_tuple = tuple(target_dept_ids)
                t_sql = text(f"SELECT id, ad_soyad, gorev FROM personel WHERE durum = 'AKTİF' AND departman_id IN {ids_tuple} ORDER BY ad_soyad")
                params = {}

            pers_data = run_query(t_sql, params=params)

            if not pers_data.empty:
                s_sql = text(f"SELECT personel_id, vardiya, izin_gunleri, aciklama FROM personel_vardiya_programi WHERE baslangic_tarihi = '{p_start}' AND bitis_tarihi = '{p_end}'")
                existing_sch = run_query(s_sql)

                merged_df = pd.merge(pers_data, existing_sch, left_on='id', right_on='personel_id', how='left')
                edit_df = merged_df.copy()
                edit_df['vardiya'] = edit_df['vardiya'].fillna("GÜNDÜZ VARDİYASI")
                edit_df['izin_gunleri'] = edit_df['izin_gunleri'].fillna("")
                edit_df['aciklama'] = edit_df['aciklama'].fillna("")
                edit_df['secim'] = True

                st.info(f"📋 **{dept_options[secilen_bolum_id]}** bölümünde {len(edit_df)} personel listeleniyor.")

                edited_schedule = st.data_editor(
                    edit_df,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    key=f"shed_editor_{secilen_bolum_id}_{p_start}",
                    column_config={
                        "id": None, "personel_id": None,
                        "secim": st.column_config.CheckboxColumn("Kaydet", width="small", default=True),
                        "ad_soyad": st.column_config.TextColumn("Personel", width="medium", disabled=True),
                        "gorev": st.column_config.TextColumn("Görev", width="small", disabled=True),
                        "vardiya": st.column_config.SelectboxColumn(
                            "Vardiya", options=["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"],
                            width="medium", required=True
                        ),
                        "izin_gunleri": st.column_config.SelectboxColumn(
                            "Haftalık İzin", options=["Pazar", "Cumartesi,Pazar", "Cumartesi", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"],
                            width="medium"
                        ),
                        "aciklama": st.column_config.TextColumn("Açıklama", width="large")
                    }
                )

                if st.button("💾 Seçilenleri Kaydet/Güncelle", type="primary"):
                    if p_end < p_start:
                        st.error("⚠️ Bitiş tarihi başlangıç tarihinden önce olamaz.")
                    else:
                        count = 0
                        with engine.connect() as conn:
                            for _, row in edited_schedule.iterrows():
                                if row['secim']:
                                    # Önce SİL sonra EKLE (Overwrite)
                                    conn.execute(text("DELETE FROM personel_vardiya_programi WHERE personel_id=:p AND baslangic_tarihi=:s AND bitis_tarihi=:e"), 
                                               {"p": row['id'], "s": p_start, "e": p_end})
                                    conn.execute(text("""
                                        INSERT INTO personel_vardiya_programi (personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri, aciklama)
                                        VALUES (:p, :s, :e, :v, :i, :n)
                                    """), {"p": row['id'], "s": p_start, "e": p_end, "v": row['vardiya'], "i": str(row['izin_gunleri']), "n": row['aciklama']})
                                    count += 1
                            conn.commit()
                        if count > 0:
                            st.success(f"✅ {count} personel programı güncellendi!"); time.sleep(1); st.rerun()
            else:
                st.warning("⚠️ Bu bölümde aktif personel bulunamadı.")
        except Exception as e: st.error(f"Hata: {e}")
    else:
        st.info("👈 Lütfen işlem yapmak istediğiniz bölümü seçin.")

def _render_personel_form(engine, dept_options, yonetici_options):
    st.subheader("👤 Personel Bilgilerini Yönet")
    pers_df_raw = veri_getir("personel")
    mod = st.radio("İşlem Modu", ["➕ Yeni Personel Ekle", "✏️ Mevcut Personeli Düzenle"], horizontal=True)

    selected_row = {}
    selected_pers_id = None

    if mod == "✏️ Mevcut Personeli Düzenle" and not pers_df_raw.empty:
        pers_dict = dict(zip(pers_df_raw['id'], pers_df_raw['ad_soyad']))
        selected_pers_id = st.selectbox("Düzenlenecek Personel", options=pers_dict.keys(), format_func=lambda x: f"{pers_dict[x]} (ID: {x})")
        selected_row = pers_df_raw[pers_df_raw['id'] == selected_pers_id].iloc[0]

    with st.form("personel_detay_form"):
        c1, c2 = st.columns(2)
        p_ad_soyad = c1.text_input("Ad Soyad", value=selected_row.get('ad_soyad', ""))
        p_gorev = c2.text_input("Görev / Unvan", value=selected_row.get('gorev', ""))
        p_durum = c2.selectbox("Durum", ["AKTİF", "PASİF"], index=0 if selected_row.get('durum') != "PASİF" else 1)

        c3, c4 = st.columns(2)
        p_dept_id = c3.selectbox("Departman", options=list(dept_options.keys()), index=list(dept_options.keys()).index(selected_row.get('departman_id')) if selected_row.get('departman_id') in dept_options else 0, format_func=lambda x: dept_options[x])
        p_yonetici_id = c4.selectbox("Bağlı Olduğu Yönetici", options=list(yonetici_options.keys()), index=list(yonetici_options.keys()).index(selected_row.get('yonetici_id')) if selected_row.get('yonetici_id') in yonetici_options else 0, format_func=lambda x: yonetici_options[x])

        pozisyon_options = {k: f"{k} - {v['name']}" for k,v in POSITION_LEVELS.items()}
        mevcut_seviye = int(selected_row.get('pozisyon_seviye', 6)) if pd.notna(selected_row.get('pozisyon_seviye')) else 6
        p_pozisyon = c3.selectbox("📊 Hiyerarşi Seviyesi", options=list(pozisyon_options.keys()), index=mevcut_seviye if mevcut_seviye in pozisyon_options else 6, format_func=lambda x: pozisyon_options[x])

        c5, col_ig = st.columns(2)
        p_giris = c5.date_input("İşe Giriş Tarihi", value=pd.to_datetime(selected_row.get('ise_giris_tarihi')).date() if pd.notna(selected_row.get('ise_giris_tarihi')) and selected_row.get('ise_giris_tarihi') != "" else datetime.now().date())
        p_servis = col_ig.text_input("Servis Durağı", value=selected_row.get('servis_duragi', ""))
        p_tel = st.text_input("Telefon No", value=selected_row.get('telefon_no', ""))

        if st.form_submit_button("💾 Personel Kaydet", use_container_width=True):
            if p_ad_soyad:
                try:
                    p_yon_val = robust_id_clean(p_yonetici_id)
                    p_dept_val = robust_id_clean(p_dept_id)
                    p_rol = "Admin" if p_pozisyon <= 1 else "ÜRETİM MÜDÜRÜ" if p_pozisyon <= 3 else "BÖLÜM SORUMLUSU" if p_pozisyon <= 5 else "Personel"
                    p_dept_name = dept_options.get(p_dept_id, "Tanımsız").replace(".. ", "").replace("↳ ", "").strip()

                    with engine.connect() as conn:
                        if selected_pers_id:
                            sql = text("""UPDATE personel SET ad_soyad=:a, gorev=:g, departman_id=:d, bolum=:bn, yonetici_id=:y, durum=:st, pozisyon_seviye=:ps, rol=:r, ise_giris_tarihi=:ig, servis_duragi=:sd, telefon_no=:tn WHERE id=:id""")
                            conn.execute(sql, {"a":p_ad_soyad, "g":p_gorev, "d":p_dept_val, "bn":p_dept_name, "y":p_yon_val, "st":p_durum, "ps":p_pozisyon, "r":p_rol, "ig":str(p_giris), "sd":p_servis, "tn":p_tel, "id":selected_pers_id})
                        else:
                            sql = text("""INSERT INTO personel (ad_soyad, gorev, departman_id, bolum, yonetici_id, durum, pozisyon_seviye, rol, ise_giris_tarihi, servis_duragi, telefon_no) VALUES (:a, :g, :d, :bn, :y, :st, :ps, :r, :ig, :sd, :tn)""")
                            conn.execute(sql, {"a":p_ad_soyad, "g":p_gorev, "d":p_dept_val, "bn":p_dept_name, "y":p_yon_val, "st":p_durum, "ps":p_pozisyon, "r":p_rol, "ig":str(p_giris), "sd":p_servis, "tn":p_tel})
                        conn.commit()
                    clear_personnel_cache()
                    st.success("✅ Kaydedildi!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Hata: {e}")
            else: st.warning("Ad Soyad zorunludur.")

def _render_personel_listesi(engine, dept_id_to_name, yonetici_id_to_name):
    # Bu fonksiyon app.py line 957-1342 arasını kapsar. 
    # Kodun geri kalanını ekliyorum.
    pers_df = run_query("SELECT * FROM personel")
    dept_name_list = list(dept_id_to_name.values())
    yonetici_name_list = ["- Yok -"] + list(yonetici_id_to_name.values())
    seviye_list = [f"{k} - {v['name']}" for k,v in sorted(POSITION_LEVELS.items())]

    pers_df['departman_adi'] = pers_df['departman_id'].fillna(0).astype(int).map(dept_id_to_name).fillna("- Seçiniz -")
    pers_df['yonetici_adi'] = pers_df['yonetici_id'].fillna(0).astype(int).map({v: k for k, v in yonetici_id_to_name.items()}).fillna("- Yok -") # Düzeltildi
    # Map yönetici isimleri için ters sözlük yerine direkt ID mapping kullanmalı
    pers_df['yonetici_adi'] = pers_df['yonetici_id'].fillna(0).astype(int).map(yonetici_id_to_name).fillna("- Yok -")

    pers_df['pozisyon_adi'] = pers_df['pozisyon_seviye'].apply(lambda x: seviye_list[int(x)] if pd.notna(x) and 0 <= int(x) <= 7 else "6 - Personel (Varsayılan)")

    edited_pers = st.data_editor(
        pers_df, num_rows="dynamic", use_container_width=True, key="editor_personel_main_ui",
        column_config={
            "id": None, "sifre": None, "rol": None, "departman_id": None, "yonetici_id": None,
            "kat": None,
            "departman_adi": st.column_config.SelectboxColumn("🏭 Departman", options=dept_name_list, required=True),
            "ad_soyad": st.column_config.TextColumn("Ad Soyad", width="medium"),
            "kullanici_adi": st.column_config.TextColumn("🔑 Kullanıcı Adı", width="medium"),
            "yonetici_adi": st.column_config.SelectboxColumn("👔 Yönetici", options=yonetici_name_list),
            "pozisyon_adi": st.column_config.SelectboxColumn("📊 Pozisyon", options=seviye_list),
            "durum": st.column_config.SelectboxColumn("Durum", options=["AKTİF", "PASİF"]),
            "bolum": None, "vardiya": None, "ise_giris_tarihi": st.column_config.TextColumn("İşe Giriş")
        }
    )

    if st.button("💾 Personel Listesini Kaydet (Toplu)", use_container_width=True):
        # Mükerrer kontrolü ve ID dönüşümü (app.py'deki logic)
        name_to_id_map = {v: k for k, v in dept_id_to_name.items()}
        name_to_sup_map = {v: k for k, v in yonetici_id_to_name.items()}

        edited_pers['departman_id'] = edited_pers['departman_adi'].map(name_to_id_map).apply(robust_id_clean)
        edited_pers['yonetici_id'] = edited_pers['yonetici_adi'].map(name_to_sup_map).apply(robust_id_clean)
        edited_pers['pozisyon_seviye'] = edited_pers['pozisyon_adi'].apply(lambda x: int(x.split(' - ')[0]) if pd.notna(x) and ' - ' in str(x) else 6)
        
        try:
            with engine.begin() as conn:
                for _, row in edited_pers.iterrows():
                    if pd.notna(row.get('id')):
                        # Anayasa Madde 1 & 5: Otomatik Rol Atama (Dinamik referans gerekse de şu an form ile eşitliyoruz)
                        p_ps = int(row['pozisyon_seviye'])
                        p_rol = "Admin" if p_ps <= 1 else "ÜRETİM MÜDÜRÜ" if p_ps <= 3 else "BÖLÜM SORUMLUSU" if p_ps <= 5 else "Personel"
                        p_dept_name = str(row['departman_adi']).replace(".. ", "").replace("↳ ", "").strip()

                        sql = text("""
                            UPDATE personel SET 
                                ad_soyad=:a, departman_id=:d, bolum=:bn, yonetici_id=:y, 
                                pozisyon_seviye=:ps, rol=:r, gorev=:g, durum=:st,
                                ise_giris_tarihi=:ig, servis_duragi=:sd, telefon_no=:tn 
                            WHERE id=:id
                        """)
                        conn.execute(sql, {
                            "a":row['ad_soyad'], "d":row['departman_id'], "bn":p_dept_name, "y":row['yonetici_id'], 
                            "ps":p_ps, "r":p_rol, "g":row['gorev'], "st":row['durum'],
                            "ig":str(row['ise_giris_tarihi']), "sd":row['servis_duragi'], "tn":row['telefon_no'], "id":row['id']
                        })
            clear_personnel_cache(); st.success("✅ Toplu Güncelleme Başarılı!"); time.sleep(1); st.rerun()
        except Exception as e: st.error(f"Hata: {e}")

def render_kullanici_tab(engine):
    st.subheader("🔐 Kullanıcı Yetki ve Şifre Yönetimi")
    try:
        rol_listesi = run_query("SELECT rol_adi FROM ayarlar_roller WHERE aktif = TRUE")['rol_adi'].tolist()
    except: rol_listesi = ["ADMIN", "PERSONEL"]

    # Yeni Kullanıcı Ekleme
    with st.expander("➕ Sisteme Yeni Kullanıcı Ekle"):
        fabrika_personel_df = run_query("SELECT p.*, COALESCE(d.bolum_adi, 'Tanımsız') as bolum_adi_display FROM personel p LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id ORDER BY p.ad_soyad")
        if not fabrika_personel_df.empty:
            personel_dict = dict(zip(fabrika_personel_df['id'], fabrika_personel_df['ad_soyad'] + " (" + fabrika_personel_df['bolum_adi_display'] + ")"))
            secilen_personel_id = st.selectbox("👤 Personel Seçin", options=fabrika_personel_df['id'].tolist(), format_func=lambda x: personel_dict.get(x, f"ID: {x}"))
            secilen_row = fabrika_personel_df[fabrika_personel_df['id'] == secilen_personel_id].iloc[0]
            
            with st.form("new_user_form_ui"):
                col1, col2 = st.columns(2)
                n_user = col1.text_input("🔑 Kullanıcı Adı", value=suggest_username(secilen_row['ad_soyad']))
                n_pass = col2.text_input("🔒 Şifre", type="password")
                n_rol = st.selectbox("🎭 Yetki Rolü", rol_listesi)
                if st.form_submit_button("✅ Kaydet"):
                    with engine.connect() as conn:
                        conn.execute(text("UPDATE personel SET kullanici_adi=:k, sifre=:s, rol=:r, durum='AKTİF' WHERE id=:pid"), {"k":n_user, "s":n_pass, "r":n_rol, "pid":secilen_personel_id})
                        conn.commit()
                    clear_personnel_cache(); st.success("✅ Yetkilendirildi!"); time.sleep(1); st.rerun()

    st.divider()
    # Mevcut Kullanıcı Listesi Editörü (Yetki dahilinde)
    user_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper()
    if user_rol in ["ADMIN", "SİSTEM ADMİN", "YÖNETİM", "GIDA MÜHENDİSİ"]:
        users_df = run_query("SELECT p.kullanici_adi, p.sifre, p.rol, p.ad_soyad, p.durum FROM personel p WHERE p.kullanici_adi IS NOT NULL")
        edited_users = st.data_editor(users_df, use_container_width=True, hide_index=True)
        if st.button("💾 Kullanıcıları Güncelle"):
            with engine.connect() as conn:
                for _, row in edited_users.iterrows():
                    conn.execute(text("UPDATE personel SET sifre=:s, rol=:r, durum=:d WHERE kullanici_adi=:k"), {"s":row['sifre'], "r":row['rol'], "d":row['durum'], "k":row['kullanici_adi']})
                conn.commit()
            clear_personnel_cache(); st.success("✅ Güncellendi!"); time.sleep(1); st.rerun()
