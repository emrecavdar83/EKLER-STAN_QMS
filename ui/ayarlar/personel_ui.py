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
from logic.auth_logic import kullanici_yetkisi_var_mi, normalize_role_string, sifre_hashle
from constants import POSITION_LEVELS, MANAGEMENT_LEVELS, get_position_label

def _rol_seviyeden_belirle(pozisyon_seviyesi):
    """Pozisyon seviyesinden rol adı türetir. ANAYASA: CONSTANTS.py'den."""
    seviye = int(pozisyon_seviyesi) if pd.notna(pozisyon_seviyesi) else 6
    if seviye in MANAGEMENT_LEVELS[:2]:
        return "ADMIN"
    elif seviye in MANAGEMENT_LEVELS[2:4]:
        return "ÜRETİM MÜDÜRÜ"
    elif seviye in MANAGEMENT_LEVELS[4:]:
        return "BÖLÜM SORUMLUSU"
    return "PERSONEL"

def _get_vardiya_tipleri():
    try:
        df = run_query("SELECT tip_adi FROM vardiya_tipleri WHERE aktif = 1 ORDER BY sira_no")
        if not df.empty: return df['tip_adi'].tolist()
    except: pass
    return ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"]

def _get_izin_gun_tipleri():
    try:
        df = run_query("SELECT tip_adi FROM izin_gunleri_tipleri WHERE aktif = 1 ORDER BY sira_no")
        if not df.empty: return df['tip_adi'].tolist()
    except: pass
    return ["Pazar", "Cumartesi,Pazar", "Cumartesi", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]

def render_personnel_tabs(engine):
    """Ayarlar modülü altındaki Personel ve Kullanıcı sekmelerini render eder."""
    
    # Bu fonksiyon hem tab1 hem de tab2 içeriğini bir wrapper olarak sunabilir 
    # veya ayrı fonksiyonlarda çağrılabilir. 
    # app.py'deki st.tabs yapısına uygun olarak bölüyoruz.
    pass

def render_personel_tab(engine):
    st.subheader("👷 Fabrika Personel Listesi Yönetimi")

    # Alt sekmeler: Form ve Tablo
    p_tabs = ["📅 Vardiya Çalışma Programı", "📝 Personel Ekle/Düzenle", "📋 Tüm Personel Listesi", "🗑️ Hatalı Kayıt Sil"]

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

    # >>> SEKME: HATALI KAYIT SİL <<<
    elif p_selected_tab == p_tabs[3]:
        _render_personel_sil_formu(engine)

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
                t_sql = "SELECT id, ad_soyad, gorev FROM personel WHERE durum = 'AKTİF' AND departman_id = :d ORDER BY ad_soyad"
                params = {"d": target_dept_ids[0]}
            else:
                ids_tuple = tuple(target_dept_ids)
                t_sql = f"SELECT id, ad_soyad, gorev FROM personel WHERE durum = 'AKTİF' AND departman_id IN {ids_tuple} ORDER BY ad_soyad"
                params = {}

            pers_data = run_query(t_sql, params=params)

            if not pers_data.empty:
                s_sql = "SELECT personel_id, vardiya, izin_gunleri, aciklama FROM personel_vardiya_programi WHERE baslangic_tarihi = :s AND bitis_tarihi = :e"
                existing_sch = run_query(s_sql, params={"s": str(p_start), "e": str(p_end)})

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
                            "Vardiya", options=_get_vardiya_tipleri(),
                            width="medium", required=True
                        ),
                        "izin_gunleri": st.column_config.SelectboxColumn(
                            "Haftalık İzin", options=_get_izin_gun_tipleri(),
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
                        try:
                            with engine.begin() as conn:
                                for _, row in edited_schedule.iterrows():
                                    if row['secim']:
                                        conn.execute(text("DELETE FROM personel_vardiya_programi WHERE personel_id=:p AND baslangic_tarihi=:s AND bitis_tarihi=:e"), 
                                                   {"p": row['id'], "s": p_start, "e": p_end})
                                        conn.execute(text("""
                                            INSERT INTO personel_vardiya_programi (personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri, aciklama)
                                            VALUES (:p, :s, :e, :v, :i, :n)
                                        """), {"p": row['id'], "s": p_start, "e": p_end, "v": row['vardiya'], "i": str(row['izin_gunleri']), "n": row['aciklama']})
                                        count += 1
                                conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('VARDIYA_PROGRAMI_GUNCELLE', :d)"), {"d": f"{count} personelin vardiya programı güncellendi."})
                            if count > 0:
                                st.toast(f"✅ {count} personel programı güncellendi!"); st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt Hatası (Sıfır Risk): {e}")
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

    with st.form(f"personel_detay_form_{selected_pers_id}"):
        # Alt-Bileşenlere Parçalama (Madde 2)
        p_data = _input_temel_bilgiler(selected_row)
        p_hiyerarsi = _input_hiyerarsi_bilgileri(selected_row, dept_options, yonetici_options)
        p_saha = _input_saha_atamasi(selected_row, dept_options, yonetici_options)
        p_kisisel = _input_kisisel_bilgiler(selected_row)

        if st.form_submit_button("💾 Personel Kaydet", use_container_width=True):
            _personel_form_kaydet_tetikle(engine, selected_pers_id, p_data, p_hiyerarsi, p_saha, p_kisisel, dept_options)

def _input_temel_bilgiler(row):
    c1, c2 = st.columns(2)
    ad_soyad = c1.text_input("Ad Soyad", value=row.get('ad_soyad', ""))
    gorev = c2.text_input("Görev / Unvan", value=row.get('gorev', ""))
    durum = c2.selectbox("Durum", ["AKTİF", "PASİF"], index=0 if row.get('durum') != "PASİF" else 1)
    return {"ad_soyad": ad_soyad, "gorev": gorev, "durum": durum}

def _input_hiyerarsi_bilgileri(row, depts, yons):
    c3, c4 = st.columns(2)
    dept_id = c3.selectbox("Departman", options=list(depts.keys()), index=list(depts.keys()).index(row.get('departman_id')) if row.get('departman_id') in depts else 0, format_func=lambda x: depts[x])
    yonetici_id = c4.selectbox("Bağlı Olduğu Yönetici", options=list(yons.keys()), index=list(yons.keys()).index(row.get('yonetici_id')) if row.get('yonetici_id') in yons else 0, format_func=lambda x: yons[x])
    
    pozisyon_options = {k: get_position_label(k) for k in POSITION_LEVELS.keys()}
    mevcut_seviye = int(row.get('pozisyon_seviye', 6)) if pd.notna(row.get('pozisyon_seviye')) else 6
    pozisyon = st.selectbox("📊 Hiyerarşi Seviyesi", options=list(pozisyon_options.keys()), index=mevcut_seviye if mevcut_seviye in pozisyon_options else 6, format_func=lambda x: pozisyon_options[x])
    return {"dept_id": dept_id, "yonetici_id": yonetici_id, "pozisyon": pozisyon}

def _input_saha_atamasi(row, depts, yons):
    st.markdown("##### 🌐 Dinamik Matris Bilgileri (Saha Ataması)")
    c_mat1, c_mat2 = st.columns(2)
    oper_dept_id = c_mat1.selectbox("📍 Saha Görev Yeri", options=list(depts.keys()), index=list(depts.keys()).index(row.get('operasyonel_bolum_id')) if row.get('operasyonel_bolum_id') in depts else 0, format_func=lambda x: depts[x])
    sec_yon_id = c_mat2.selectbox("👔 Saha Sorumlusu", options=list(yons.keys()), index=list(yons.keys()).index(row.get('ikincil_yonetici_id')) if row.get('ikincil_yonetici_id') in yons else 0, format_func=lambda x: yons[x])
    return {"oper_dept_id": oper_dept_id, "sec_yon_id": sec_yon_id}

def _input_kisisel_bilgiler(row):
    c1, c2 = st.columns(2)
    giris = c1.date_input("İşe Giriş Tarihi", value=pd.to_datetime(row.get('ise_giris_tarihi')).date() if pd.notna(row.get('ise_giris_tarihi')) and row.get('ise_giris_tarihi') != "" else datetime.now().date())
    servis = c2.text_input("Servis Durağı", value=row.get('servis_duragi', ""))
    tel = st.text_input("Telefon No", value=row.get('telefon_no', ""))
    return {"ise_giris": giris, "servis": servis, "tel": tel}

def _personel_form_kaydet_tetikle(engine, p_id, data, hiyerarşi, saha, kisisel, dept_options):
    if not data['ad_soyad']:
        st.warning("Ad Soyad zorunludur."); return
        
    try:
        p_rol = normalize_role_string(_rol_seviyeden_belirle(hiyerarşi['pozisyon']))
        p_dept_name = dept_options.get(hiyerarşi['dept_id'], "Tanımsız").replace(".. ", "").replace("↳ ", "").strip()

        with engine.begin() as conn:
            params = {
                "a": data['ad_soyad'], "g": data['gorev'], "d": hiyerarşi['dept_id'], "bn": p_dept_name,
                "y": hiyerarşi['yonetici_id'], "st": data['durum'], "ps": hiyerarşi['pozisyon'],
                "r": p_rol, "ig": str(kisisel['ise_giris']), "sd": kisisel['servis'], "tn": kisisel['tel'],
                "ob": saha['oper_dept_id'], "iy": saha['sec_yon_id']
            }
            if p_id:
                params["id"] = int(p_id)
                sql = text("""UPDATE personel SET ad_soyad=:a, gorev=:g, departman_id=:d, bolum=:bn, yonetici_id=:y, durum=:st, pozisyon_seviye=:ps, rol=:r, ise_giris_tarihi=:ig, servis_duragi=:sd, telefon_no=:tn, operasyonel_bolum_id=:ob, ikincil_yonetici_id=:iy, guncelleme_tarihi=CURRENT_TIMESTAMP WHERE id=:id""")
                conn.execute(sql, params)
                conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('PERSONEL_GUNCELLE', :dx)"), {"dx": f"Personel (ID: {p_id}) güncellendi."})
            else:
                sql = text("""INSERT INTO personel (ad_soyad, gorev, departman_id, bolum, yonetici_id, durum, pozisyon_seviye, rol, ise_giris_tarihi, servis_duragi, telefon_no, operasyonel_bolum_id, ikincil_yonetici_id) VALUES (:a, :g, :d, :bn, :y, :st, :ps, :r, :ig, :sd, :tn, :ob, :iy)""")
                conn.execute(sql, params)
                conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('PERSONEL_EKLE', :dx)"), {"dx": f"Yeni personel: {data['ad_soyad']}"})
        clear_personnel_cache(); st.toast("✅ Personel Kaydedildi!"); st.rerun()
    except Exception as e: st.error(f"Kayıt Hatası: {e}")

def _render_personel_listesi(engine, dept_id_to_name, yonetici_id_to_name):
    """Personel listesini zırhlı ve hiyerarşik olarak listeler."""
    try:
        # Veriyi Hazırla (Bileşen 1)
        pers_df = _prepare_personnel_display_df(dept_id_to_name, yonetici_id_to_name)
        
        # UI Editörü (Bileşen 2)
        edited_pers = _render_personnel_editor(pers_df, dept_id_to_name, yonetici_id_to_name)

        if st.button("💾 Personel Listesini Kaydet (Toplu)", use_container_width=True):
            _personel_toplu_kaydet_tetikle(engine, edited_pers, dept_id_to_name, yonetici_id_to_name)
    except Exception as e:
        st.error(f"Liste Hatası: {e}")

def _prepare_personnel_display_df(dept_id_to_name, yonetici_id_to_name):
    sql = "SELECT id, ad_soyad, kullanici_adi, rol, durum, departman_id, yonetici_id, pozisyon_seviye, ise_giris_tarihi, servis_duragi, telefon_no, operasyonel_bolum_id, ikincil_yonetici_id, gorev FROM personel"
    df = run_query(sql)
    
    seviye_list = [f"{k} - {v['name']}" for k,v in sorted(POSITION_LEVELS.items())]
    
    # Mapping İşlemleri
    df['departman_adi'] = df['departman_id'].fillna(0).astype(int).map(dept_id_to_name).fillna("- Seçiniz -")
    df['yonetici_adi'] = df['yonetici_id'].fillna(0).astype(int).map(yonetici_id_to_name).fillna("- Yok -")
    df['oper_bolum_adi'] = df['operasyonel_bolum_id'].fillna(0).astype(int).map(dept_id_to_name).fillna("- Yok -")
    df['sec_yonetici_adi'] = df['ikincil_yonetici_id'].fillna(0).astype(int).map(yonetici_id_to_name).fillna("- Yok -")
    df['pozisyon_adi'] = df['pozisyon_seviye'].apply(lambda x: seviye_list[int(x)] if pd.notna(x) and 0 <= int(x) <= 7 else "6 - Personel (Varsayılan)")
    return df

def _render_personnel_editor(df, dept_map, yonetici_map):
    dept_names = list(dept_map.values())
    yonetici_names = ["- Yok -"] + list(yonetici_map.values())
    seviye_list = [f"{k} - {v['name']}" for k,v in sorted(POSITION_LEVELS.items())]

    return st.data_editor(
        df, num_rows="dynamic", use_container_width=True, key="editor_personel_main_ui",
        column_config={
            "id": None, "sifre": None, "rol": None, "departman_id": None, "yonetici_id": None,
            "kat": None, "operasyonel_bolum_id": None, "ikincil_yonetici_id": None,
            "departman_adi": st.column_config.SelectboxColumn("🏭 Fonksiyonel Dept", options=dept_names, required=True),
            "ad_soyad": st.column_config.TextColumn("Ad Soyad", width="medium"),
            "kullanici_adi": st.column_config.TextColumn("🔑 Kullanıcı Adı", width="medium"),
            "yonetici_adi": st.column_config.SelectboxColumn("👔 Hiyerarşik Üst", options=yonetici_names),
            "oper_bolum_adi": st.column_config.SelectboxColumn("📍 Saha Görev Yeri", options=dept_names),
            "sec_yonetici_adi": st.column_config.SelectboxColumn("🛡️ Saha Sorumlusu", options=yonetici_names),
            "pozisyon_adi": st.column_config.SelectboxColumn("📊 Pozisyon", options=seviye_list),
            "durum": st.column_config.SelectboxColumn("Durum", options=["AKTİF", "PASİF"]),
            "bolum": None, "ise_giris_tarihi": st.column_config.TextColumn("İşe Giriş")
        }
    )

def _personel_toplu_kaydet_tetikle(engine, edited_df, dept_id_to_name, yonetici_id_to_name):
    # ID Dönüşümü
    name_to_id = {v: k for k, v in dept_id_to_name.items()}
    name_to_yid = {v: k for k, v in yonetici_id_to_name.items()}

    edited_df['departman_id'] = edited_df['departman_adi'].map(name_to_id).apply(robust_id_clean)
    edited_df['yonetici_id'] = edited_df['yonetici_adi'].map(name_to_yid).apply(robust_id_clean)
    edited_df['operasyonel_bolum_id'] = edited_df['oper_bolum_adi'].map(name_to_id).apply(robust_id_clean)
    edited_df['ikincil_yonetici_id'] = edited_df['sec_yonetici_adi'].map(name_to_yid).apply(robust_id_clean)
    edited_df['pozisyon_seviye'] = edited_df['pozisyon_adi'].apply(lambda x: int(x.split(' - ')[0]) if pd.notna(x) and ' - ' in str(x) else 6)
    
    try:
        with engine.begin() as conn:
            for _, row in edited_df.iterrows():
                if pd.notna(row.get('id')):
                    _update_single_personel(conn, row)
            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('PERSONEL_TOPLU_GUNCELLE', 'OK')"))
        clear_personnel_cache(); st.toast("✅ Başarılı!"); st.rerun()
    except Exception as e: st.error(f"Hata: {e}")

def _update_single_personel(conn, row):
    p_id = int(row['id'])
    p_rol = normalize_role_string(_rol_seviyeden_belirle(row['pozisyon_seviye']))
    p_dept_name = str(row['departman_adi']).replace(".. ", "").replace("↳ ", "").strip()
    
    sql = text("""UPDATE personel SET ad_soyad=:a, departman_id=:d, bolum=:bn, yonetici_id=:y, pozisyon_seviye=:ps, rol=:r, gorev=:g, durum=:st, ise_giris_tarihi=:ig, servis_duragi=:sd, telefon_no=:tn, operasyonel_bolum_id=:ob, ikincil_yonetici_id=:iy, guncelleme_tarihi=CURRENT_TIMESTAMP WHERE id=:id""")
    conn.execute(sql, {
        "a":row['ad_soyad'], "d":row['departman_id'], "bn":p_dept_name, "y":row['yonetici_id'], 
        "ps":row['pozisyon_seviye'], "r":p_rol, "g":row['gorev'], "st":row['durum'],
        "ig":str(row['ise_giris_tarihi']), "sd":row['servis_duragi'], "tn":row['telefon_no'], 
        "ob":row['operasyonel_bolum_id'], "iy":row['ikincil_yonetici_id'], "id":p_id
    })
def _bagimliliklari_kontrol(engine, personel_id):
    """Silinecek personelin bağımlı kayıt sayılarını döner."""
    tablolar = {
        'personel_vardiya_programi': 'Vardiya Programı',
        'personnel_tasks':           'Görev Kaydı',
        'qdms_okuma_onay':           'Belge Onayı',
        'polivalans_matris':         'Polivalans Matris',
        'performans_degerledirme':   'Performans Değerlendirme',
        'flow_bypass_logs':          'Denetim İzi',
    }
    sonuc = {}
    with engine.connect() as conn:
        for tbl, etiket in tablolar.items():
            try:
                n = conn.execute(
                    text(f"SELECT COUNT(*) FROM {tbl} WHERE personel_id=:p"),
                    {"p": personel_id}
                ).scalar()
                if n: sonuc[etiket] = n
            except Exception:
                pass
    return sonuc


def _personel_guvvenli_sil(engine, personel_id, ad_soyad, cascade):
    """Bağımlı kayıtlarla birlikte personeli siler ve loglar."""
    with engine.begin() as conn:
        if cascade:
            conn.execute(text(
                "DELETE FROM personel_vardiya_programi WHERE personel_id=:p"
            ), {"p": personel_id})
            conn.execute(text(
                "DELETE FROM personnel_tasks WHERE personel_id=:p"
            ), {"p": personel_id})
        conn.execute(text("DELETE FROM personel WHERE id=:p"), {"p": personel_id})
        conn.execute(text(
            "INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('PERSONEL_SIL',:d)"
        ), {"d": f"Silinen: {ad_soyad} (ID:{personel_id}) — cascade:{cascade}"})


def _render_personel_sil_formu(engine):
    """Hatalı kayıt silme arayüzü — bağımlılık kontrolü ile."""
    if not kullanici_yetkisi_var_mi("Ayarlar", "Yönet"):
        return
    with st.expander("🗑️ Hatalı Kayıt Sil", expanded=False):
        st.warning("Bu işlem geri alınamaz. Sadece hatalı / test girişleri için kullanın.")
        pers_df = run_query(
            "SELECT id, ad_soyad, rol, durum, ise_giris_tarihi FROM personel ORDER BY ad_soyad"
        )
        if pers_df.empty:
            return
        secenekler = {f"{r['ad_soyad']} ({r['durum']})": r['id'] for _, r in pers_df.iterrows()}
        secim = st.selectbox("Silinecek personeli seç", list(secenekler.keys()), key="sil_secim")
        if not secim:
            return
        p_id   = secenekler[secim]
        p_adi  = secim.split(" (")[0]
        baglar = _bagimliliklari_kontrol(engine, p_id)
        if baglar:
            st.warning("Bağımlı kayıtlar da silinecek:")
            for etiket, n in baglar.items():
                st.write(f"  • {etiket}: **{n}** kayıt")
        else:
            st.success("Bağımlı kayıt yok — güvenle silinebilir.")
        onay = st.text_input(
            f'Onaylamak için **"{p_adi}"** yazın', key="sil_onay"
        )
        if st.button("🗑️ Kalıcı Olarak Sil", type="primary", key="sil_btn"):
            import unicodedata
            _norm = lambda s: unicodedata.normalize('NFC', s.strip().upper())
            if _norm(onay) != _norm(p_adi):
                st.error(f"Ad eşleşmedi. Beklenen: '{p_adi}'")
                return
            try:
                _personel_guvvenli_sil(engine, p_id, p_adi, cascade=True)
                clear_personnel_cache()
                st.success(f"✅ {p_adi} silindi.")
                st.rerun()
            except Exception as e:
                st.error(f"Silme hatası: {e}")


def render_kullanici_tab(engine):
    st.subheader("🔐 Kullanıcı Yetki ve Şifre Yönetimi")
    try:
        rol_listesi = run_query("SELECT rol_adi FROM ayarlar_roller WHERE aktif = 1")['rol_adi'].tolist()
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
                # v4.4.2: UI Seviyesinde 72-byte Barajı (max_chars=64)
                n_pass = col2.text_input("🔒 Şifre", type="password", max_chars=64, help="Güvenlik nedeniyle şifre en fazla 64 karakter olabilir.")
                n_rol = st.selectbox("🎭 Yetki Rolü", rol_listesi)
                if st.form_submit_button("✅ Kaydet"):
                    try:
                        with engine.begin() as conn:
                            fixed_rol = normalize_role_string(n_rol)
                            # Anayasa v3.2: Şifreyi kaydetmeden önce hashle
                            hashed_pass = sifre_hashle(n_pass)
                            conn.execute(text("UPDATE personel SET kullanici_adi=:k, sifre=:s, rol=:r, durum='AKTİF' WHERE id=:pid"), {"k":n_user, "s":hashed_pass, "r":fixed_rol, "pid":int(secilen_personel_id)})
                            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('KULLANICI_YETKILENDIRME', :d)"), {"d": f"Personel (ID: {int(secilen_personel_id)}) yetkilendirildi. Rol: {fixed_rol}"})
                        clear_personnel_cache(); st.toast("✅ Yetkilendirildi!"); st.rerun()
                    except Exception as e: st.error(f"Hata: {e}")

    st.divider()
    # Mevcut Kullanıcı Listesi Editörü (Yetki dahilinde)
    if kullanici_yetkisi_var_mi("Ayarlar", "Yönet"):
        users_df = run_query("SELECT p.id, p.kullanici_adi, p.sifre, p.rol, p.ad_soyad, p.durum FROM personel p WHERE p.kullanici_adi IS NOT NULL")
        edited_users = st.data_editor(users_df, use_container_width=True, hide_index=True, column_config={"id": None})
        if st.button("💾 Kullanıcıları Güncelle"):
            try:
                with engine.begin() as conn:
                    for _, row in edited_users.iterrows():
                        fixed_rol = normalize_role_string(row['rol'])
                        # Önemli: Sadece şifre değişmişse veya düz metinse hashle
                        original_pass = users_df[users_df['id'] == row['id']]['sifre'].values[0]
                        final_pass = row['sifre']
                        if final_pass != original_pass:
                            final_pass = sifre_hashle(final_pass)
                            
                        conn.execute(text("UPDATE personel SET kullanici_adi=:k, sifre=:s, rol=:r, durum=:d, guncelleme_tarihi=CURRENT_TIMESTAMP WHERE id=:id"), 
                                   {"k":row['kullanici_adi'], "s":final_pass, "r":fixed_rol, "d":row['durum'], "id":int(row['id'])})
                    conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('KULLANICI_TOPLU_GUNCELLE', 'Kullanıcı yetkileri ID bazlı toplu güncellendi.')"))
                clear_personnel_cache(); st.toast("✅ Yetki Güncellendi!"); st.rerun()
            except Exception as e: st.error(f"Hata: {e}")
