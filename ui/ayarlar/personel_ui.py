import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
import time

from logic.data_fetcher import (
    veri_getir, run_query, get_qms_department_options_hierarchical,
    get_all_sub_department_ids, get_qms_department_tree,
    robust_id_clean
)
from logic.settings_logic import (
    suggest_username, log_personnel_transfer, log_personnel_exit
)
from logic.cache_manager import clear_personnel_cache, clear_all_cache
from logic.translation_logic import translate_columns, get_tr_label
from logic.sync_handler import render_sync_button
from logic.auth_logic import kullanici_yetkisi_var_mi, normalize_role_string, sifre_hashle
from logic.dynamic_sync import sync_personnel_to_users
from constants import POSITION_LEVELS, MANAGEMENT_LEVELS, get_position_label, YONETICI_MAX_SEVIYE

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

def render_personel_tab(engine):
    # FLASH MESAJ SİSTEMİ
    if '_personel_flash' in st.session_state:
        msg = st.session_state.pop('_personel_flash')
        st.success(msg)
    st.subheader("👷 Fabrika Personel Listesi Yönetimi")

    # --- ERKEN YÜKLEME: LİSTELERİ HAZIRLA ---
    try:
        dept_options = get_qms_department_options_hierarchical()
    except Exception:
        dept_options = {0: "- Seçiniz -"}

    try:
        # v7.0.9: TÜM personel listesi - pozisyon filtreleme yok
        yon_sql = """
            SELECT id, ad_soyad
            FROM ayarlar_kullanicilar
            WHERE ad_soyad IS NOT NULL AND durum = 'AKTİF'
            ORDER BY ad_soyad
        """
        yon_df = run_query(yon_sql)
        yonetici_options = {0: "- Yok -"}
        for _, row in yon_df.iterrows():
            yonetici_options[row['id']] = row['ad_soyad']
    except Exception as e:
        yonetici_options = {0: "- Yok -"}

    # v8.7: st.radio → st.tabs (navigation state conflict fix)
    # v7.0.2: Tab persistence with selectbox (st.tabs doesn't track selection)
    if 'personel_tab_index' not in st.session_state:
        st.session_state.personel_tab_index = 1  # Default to Ekle/Düzenle

    tab_names = ["📋 Tüm Personel Listesi", "📝 Personel Ekle/Düzenle", "🗑️ Hatalı Kayıt Sil"]
    selected_tab = st.selectbox("", tab_names, index=st.session_state.personel_tab_index, label_visibility="collapsed", key="personel_tab_select")

    selected_index = tab_names.index(selected_tab)
    st.session_state.personel_tab_index = selected_index

    if selected_index == 0:
        _render_personel_listesi(engine, dept_options, yonetici_options)
    elif selected_index == 1:
        _render_personel_form(engine, dept_options, yonetici_options)
    elif selected_index == 2:
        _render_personel_sil_formu(engine)

def _render_personel_form(engine, dept_options, yonetici_options):
    st.subheader("👤 Personel Bilgilerini Yönet")
    # v6.8.9: Separation - Personnel form now pulls from the main personnel source
    pers_df_raw = veri_getir("Ayarlar_Personel_V2")
    # Form version: kayıt sonrası artar → key değişir → widget değerleri sıfırlanır
    _form_ver = st.session_state.get('_personel_form_version', 0)

    # v8.8.2: Unique key to prevent app navigation conflict when radio clicked
    mod = st.radio("İşlem Modu", ["➕ Yeni Personel Ekle", "✏️ Mevcut Personeli Düzenle"], horizontal=True, key="personel_ekle_duzenle_modu_radio")

    selected_row = {}
    selected_pers_id = None

    if mod == "✏️ Mevcut Personeli Düzenle":
        if not pers_df_raw.empty:
            try:
                pers_dict = dict(zip(pers_df_raw['id'], pers_df_raw['ad_soyad']))
                selected_pers_id = st.selectbox("Düzenlenecek Personel", options=list(pers_dict.keys()), format_func=lambda x: f"{pers_dict.get(x, 'Bilinmiyor')} (ID: {x})", key="personel_duzenle_sec")
            except KeyError as ke:
                st.error(f"❌ Sütun Hatası: {ke}. Sütunlar: {pers_df_raw.columns.tolist()}")
                selected_pers_id = None

            # v6.1.2: Zırhlı Row Erişimi - IndexError Önleyici
            filtered_rows = pers_df_raw[pers_df_raw['id'] == selected_pers_id]
            if not filtered_rows.empty:
                selected_row = filtered_rows.iloc[0]
            else:
                st.warning("Seçilen personel verisi bulunamadı.")
                selected_row = {}
        else:
            st.warning("⚠️ Personel listesi boş. Veritabanı bağlantısı kontrol edin.")
            selected_row = {}

    # v8.8.1: Stable form key (FIX: page reset when changing person selection)
    # Form key depends on mode, NOT on selected person ID, so selectbox change doesn't reset form
    form_mode = "edit" if mod == "✏️ Mevcut Personeli Düzenle" else "new"
    with st.form(f"personel_detay_form_{form_mode}_v{_form_ver}"):
        # Alt-Bileşenlere Parçalama (Madde 2)
        try:
            p_data = _input_temel_bilgiler(selected_row, selected_pers_id)
            p_hiyerarsi = _input_hiyerarsi_bilgileri(selected_row, dept_options, yonetici_options, selected_pers_id)
            p_saha = _input_saha_atamasi(selected_row, dept_options, yonetici_options, selected_pers_id)
            p_kisisel = _input_kisisel_bilgiler(selected_row, selected_pers_id)
        except Exception as e:
            st.error(f"❌ FORM OKUMA HATASI: {e}")
            return

        if st.form_submit_button("💾 Personel Kaydet", width="stretch"):
            _personel_form_kaydet_tetikle(engine, selected_pers_id, p_data, p_hiyerarsi, p_saha, p_kisisel, dept_options)

def _safe_str(val, default=""):
    return default if pd.isna(val) else str(val)

def _input_temel_bilgiler(row, p_id):
    c1, c2 = st.columns(2)
    ad_soyad = c1.text_input("Ad Soyad", value=_safe_str(row.get('ad_soyad')), key=f"ad_soyad_{p_id}")
    gorev = c2.text_input("Görev / Unvan", value=_safe_str(row.get('gorev')), key=f"gorev_{p_id}")
    durum = c2.selectbox("Durum", ["AKTİF", "PASİF"], index=0 if row.get('durum') != "PASİF" else 1, key=f"durum_{p_id}")
    
    # v5.8.2: Ayrılma Bilgileri (Madde 9)
    ayrilma_tarihi = None
    ayrilma_nedeni = ""
    if durum == "PASİF":
        c3, c4 = st.columns(2)
        try:
            _ayrilma_val = row.get('ayrilma_tarihi')
            _ayrilma_date = pd.to_datetime(_ayrilma_val).date() if pd.notna(_ayrilma_val) and str(_ayrilma_val).strip() not in ("", "None", "nan") else datetime.now().date()
        except Exception:
            _ayrilma_date = datetime.now().date()
        ayrilma_tarihi = c3.date_input("Ayrılma Tarihi", value=_ayrilma_date, key=f"ayrilma_tarihi_{p_id}")
        ayrilma_nedeni = c4.text_input("Ayrılma Nedeni", value=_safe_str(row.get('ayrilma_nedeni')), key=f"ayrilma_nedeni_{p_id}")
        
    return {"ad_soyad": ad_soyad, "gorev": gorev, "durum": durum, "ayrilma_tarihi": ayrilma_tarihi, "ayrilma_nedeni": ayrilma_nedeni}

def _input_hiyerarsi_bilgileri(row, depts, yons, p_id):
    c3, c4 = st.columns(2)
    # v8.6.3: Safe int cast for qms_departman_id (DataFrame may return float)
    _raw_dept = row.get('qms_departman_id') or row.get('departman_id')
    try:
        _dept_key = int(_raw_dept) if _raw_dept is not None and pd.notna(_raw_dept) else 0
    except (ValueError, TypeError):
        _dept_key = 0
    dept_id = c3.selectbox("Departman", options=list(depts.keys()), index=list(depts.keys()).index(_dept_key) if _dept_key in depts else 0, format_func=lambda x: depts[x], key=f"dept_id_{p_id}")

    # v7.0.2 FIX: Manager field type safety (yonetici_id was not persisting after save)
    _raw_yon = row.get('yonetici_id')
    try:
        _yon_key = int(_raw_yon) if _raw_yon is not None and pd.notna(_raw_yon) else 0
    except (ValueError, TypeError):
        _yon_key = 0

    # v7.0.6: Fallback to text input if manager list is empty
    if yons and len(yons) > 0:
        # v7.0.3 FIX: Ensure 0 (no manager) is always in options
        _yon_options = {0: "➖ Belirtilmemiş"} if 0 not in yons else {}
        _yon_options.update(yons)
        _yon_index = list(_yon_options.keys()).index(_yon_key) if _yon_key in _yon_options else 0
        yonetici_id = c4.selectbox("Bağlı Olduğu Yönetici", options=list(_yon_options.keys()), index=_yon_index, format_func=lambda x: _yon_options[x], key=f"yonetici_id_{p_id}")
    else:
        c4.info("⚠️ Yönetici listesi boş. Aşağıya yönetici ismini yazabilirsiniz.")
        yonetici_text = c4.text_input("Yönetici İsmi (Manuel)", value=row.get('yonetici_adi', ''), key=f"yonetici_text_{p_id}")
        yonetici_id = yonetici_text  # Placeholder - daha sonra ID'ye çevrilecek
    
    pozisyon_options = {k: get_position_label(k) for k in POSITION_LEVELS.keys()}
    
    sec_seviye = row.get('pozisyon_seviye', 6)
    try:
        mevcut_seviye = int(sec_seviye) if pd.notna(sec_seviye) and str(sec_seviye).strip() != "" else 6
    except:
        mevcut_seviye = 6
        
    pozisyon = st.selectbox("📊 Hiyerarşi Seviyesi", options=list(pozisyon_options.keys()), index=mevcut_seviye if mevcut_seviye in pozisyon_options else 6, format_func=lambda x: pozisyon_options[x], key=f"pozisyon_{p_id}")
    return {"dept_id": dept_id, "yonetici_id": yonetici_id, "pozisyon": pozisyon}

def _input_saha_atamasi(row, depts, yons, p_id):
    st.markdown("##### 🌐 Dinamik Matris Bilgileri (Saha Ataması)")
    c_mat1, c_mat2 = st.columns(2)

    # v7.0.2 FIX: Type safety for operasyonel_bolum_id
    _raw_oper = row.get('operasyonel_bolum_id')
    try:
        _oper_key = int(_raw_oper) if _raw_oper is not None and pd.notna(_raw_oper) else 0
    except (ValueError, TypeError):
        _oper_key = 0
    _oper_index = list(depts.keys()).index(_oper_key) if _oper_key in depts else 0
    oper_dept_id = c_mat1.selectbox("📍 Saha Görev Yeri", options=list(depts.keys()), index=_oper_index, format_func=lambda x: depts[x], key=f"oper_dept_id_{p_id}")

    # v7.0.2 FIX: Type safety for ikincil_yonetici_id
    _raw_sec_yon = row.get('ikincil_yonetici_id')
    try:
        _sec_yon_key = int(_raw_sec_yon) if _raw_sec_yon is not None and pd.notna(_raw_sec_yon) else 0
    except (ValueError, TypeError):
        _sec_yon_key = 0
    # v7.0.3 FIX: Ensure 0 (no manager) is always in options
    _sec_yon_options = {0: "➖ Belirtilmemiş"} if 0 not in yons else {}
    _sec_yon_options.update(yons)
    _sec_yon_index = list(_sec_yon_options.keys()).index(_sec_yon_key) if _sec_yon_key in _sec_yon_options else 0
    sec_yon_id = c_mat2.selectbox("👔 Saha Sorumlusu", options=list(_sec_yon_options.keys()), index=_sec_yon_index, format_func=lambda x: _sec_yon_options[x], key=f"sec_yon_id_{p_id}")
    return {"oper_dept_id": oper_dept_id, "sec_yon_id": sec_yon_id}

def _input_kisisel_bilgiler(row, p_id):
    c1, c2 = st.columns(2)
    try:
        _giris_val = row.get('ise_giris_tarihi')
        _giris_date = pd.to_datetime(_giris_val).date() if pd.notna(_giris_val) and str(_giris_val).strip() not in ("", "None", "nan") else datetime.now().date()
    except Exception:
        _giris_date = datetime.now().date()
    giris = c1.date_input("İşe Giriş Tarihi", value=_giris_date, key=f"ise_giris_tarihi_{p_id}")
    servis = c2.text_input("Servis Durağı", value=_safe_str(row.get('servis_duragi')), key=f"servis_duragi_{p_id}")
    tel = st.text_input("Telefon No", value=_safe_str(row.get('telefon_no')), key=f"telefon_no_{p_id}")
    return {"ise_giris": giris, "servis": servis, "tel": tel}

def _personel_form_kaydet_tetikle(engine, p_id, data, hiyerarşi, saha, kisisel, dept_options):
    if not data['ad_soyad']:
        st.warning("Ad Soyad zorunludur."); return
        
    try:
        p_rol = normalize_role_string(_rol_seviyeden_belirle(hiyerarşi['pozisyon']))
        p_dept_name = dept_options.get(hiyerarşi['dept_id'], "Tanımsız").replace(".. ", "").replace("↳ ", "").strip()
        current_user_id = st.session_state.get('user_id', 0)

        with engine.begin() as conn:
            # v5.8.2: Transfer Loglama (Madde 3)
            # v6.8.9: Targeted Save - Personnel records now saved to 'personel' table
            target_table = "personel" # Using 'personel' as primary data source
            
            if p_id:
                old_data = conn.execute(text(f"SELECT qms_departman_id, pozisyon_seviye, durum FROM {target_table} WHERE id=:id"), {"id": p_id}).fetchone()
                if old_data:
                    # Bölüm değiştiyse
                    if old_data[0] != hiyerarşi['dept_id']:
                        log_personnel_transfer(conn, p_id, old_data[0], hiyerarşi['dept_id'], current_user_id, "Bölüm Değişikliği")
                    
                    # Durum PASİF olduysa
                    if old_data[2] != "PASİF" and data['durum'] == "PASİF":
                        log_personnel_exit(conn, p_id, data['ayrilma_tarihi'], data['ayrilma_nedeni'], current_user_id)

            params = {
                "a": data['ad_soyad'], "g": data['gorev'],
                "d": robust_id_clean(hiyerarşi['dept_id']),
                "bn": p_dept_name,
                "y": robust_id_clean(hiyerarşi['yonetici_id']) or None,
                "st": data['durum'], "ps": hiyerarşi['pozisyon'],
                "r": p_rol, "ig": str(kisisel['ise_giris']), "sd": kisisel['servis'], "tn": kisisel['tel'],
                "ob": robust_id_clean(saha['oper_dept_id']) or None,
                "iy": robust_id_clean(saha['sec_yon_id']) or None,
                "at": data['ayrilma_tarihi'], "an": data['ayrilma_nedeni']
            }
            if p_id:
                params["id"] = int(p_id)
                sql = text(f"""UPDATE {target_table} SET ad_soyad=:a, gorev=:g, qms_departman_id=:d, departman_id=:d, bolum=:bn, yonetici_id=:y, durum=:st, pozisyon_seviye=:ps, rol=:r, ise_giris_tarihi=:ig, servis_duragi=:sd, telefon_no=:tn, operasyonel_bolum_id=:ob, ikincil_yonetici_id=:iy, ayrilma_tarihi=:at, ayrilma_nedeni=:an, guncelleme_tarihi=CURRENT_TIMESTAMP WHERE id=:id""")
                conn.execute(sql, params)

                # MADDE 2.1: %100 Dinamik Senkronizasyon — hardcoded field list YOK
                # Tüm personel alanları otomatik olarak ayarlar_kullanicilar'a senkronize olur
                sync_data = {
                    "ad_soyad": data['ad_soyad'],
                    "gorev": data['gorev'],
                    "qms_departman_id": robust_id_clean(hiyerarşi['dept_id']),
                    "departman_id": robust_id_clean(hiyerarşi['dept_id']),
                    "bolum": p_dept_name,
                    "yonetici_id": robust_id_clean(hiyerarşi['yonetici_id']) or None,
                    "durum": data['durum'],
                    "pozisyon_seviye": hiyerarşi['pozisyon'],
                    "rol": p_rol,
                    "ise_giris_tarihi": str(kisisel['ise_giris']),
                    "servis_duragi": kisisel['servis'],
                    "telefon_no": kisisel['tel'],
                    "operasyonel_bolum_id": robust_id_clean(saha['oper_dept_id']) or None,
                    "ikincil_yonetici_id": robust_id_clean(saha['sec_yon_id']) or None,
                }
                sync_result = sync_personnel_to_users(conn, p_id, sync_data)
                if not sync_result:
                    st.warning("⚠️ Personel kaydedildi ama ayarlar tablosuna senkronizasyon başarısız oldu.")

                conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay, kullanici_id) VALUES ('PERSONEL_GUNCELLE', :dx, :uid)"), {"dx": f"Personel (ID: {p_id}) güncellendi.", "uid": current_user_id})
            else:
                sql = text(f"""INSERT INTO {target_table} (ad_soyad, gorev, qms_departman_id, departman_id, bolum, yonetici_id, durum, pozisyon_seviye, rol, ise_giris_tarihi, servis_duragi, telefon_no, operasyonel_bolum_id, ikincil_yonetici_id) VALUES (:a, :g, :d, :d, :bn, :y, :st, :ps, :r, :ig, :sd, :tn, :ob, :iy)""")
                conn.execute(sql, params)
                conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay, kullanici_id) VALUES ('PERSONEL_EKLE', :dx, :uid)"), {"dx": f"Yeni personel: {data['ad_soyad']}", "uid": current_user_id})
        
        clear_personnel_cache()
        st.session_state['_personel_form_version'] = st.session_state.get('_personel_form_version', 0) + 1
        st.session_state['_personel_flash'] = "✅ Personel başarıyla kaydedildi!"
        st.rerun()
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        st.error(f"❌ KAYIT HATASI:\n{str(e)}")
        st.warning(f"**Teknik Detay:**\n```\n{error_detail}\n```")
        # Log'a yaz
        try:
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('PERSONEL_KAYIT_HATASI', :d)"),
                           {"d": f"Error: {str(e)}\n{error_detail}"})
        except: pass

def _render_personel_listesi(engine, dept_id_to_name, yonetici_id_to_name):
    """Personel listesini zırhlı ve hiyerarşik olarak listeler."""
    try:
        # Veriyi Hazırla (Bileşen 1)
        pers_df = _prepare_personnel_display_df(dept_id_to_name, yonetici_id_to_name)
        
        # UI Editörü (Bileşen 2)
        edited_pers = _render_personnel_editor(pers_df, dept_id_to_name, yonetici_id_to_name)

        if st.button("💾 Personel Listesini Kaydet (Toplu)", width="stretch"):
            _personel_toplu_kaydet_tetikle(engine, edited_pers, dept_id_to_name, yonetici_id_to_name)
    except Exception as e:
        st.error(f"Liste Hatası: {e}")

def _prepare_personnel_display_df(dept_id_to_name, yonetici_id_to_name):
    # v8.5: Reverted to 'personel' table as per user instruction for master staff list
    sql = "SELECT * FROM personel"
    df = run_query(sql)
    
    seviye_list = [f"{k} - {v['name']}" for k,v in sorted(POSITION_LEVELS.items())]
    
    def _safe_idx(val):
        try:
            # v6.8.9: Robust handling for string-based position levels (e.g. '7 - Kalite')
            clean_v = str(val).split(' - ')[0] if ' - ' in str(val) else val
            idx = int(float(clean_v))
            return idx if 0 <= idx <= 7 else 6
        except: return 6

    # Mapping İşlemleri
    df['departman_adi'] = df['qms_departman_id'].fillna(0).astype(int).map(dept_id_to_name).fillna("- Seçiniz -")
    df['yonetici_adi'] = df['yonetici_id'].fillna(0).astype(int).map(yonetici_id_to_name).fillna("- Yok -")
    df['oper_bolum_adi'] = df['operasyonel_bolum_id'].fillna(0).astype(int).map(dept_id_to_name).fillna("- Yok -")
    df['sec_yonetici_adi'] = df['ikincil_yonetici_id'].fillna(0).astype(int).map(yonetici_id_to_name).fillna("- Yok -")
    df['pozisyon_adi'] = df['pozisyon_seviye'].apply(lambda x: seviye_list[_safe_idx(x)])
    return df

def _render_personnel_editor(df, dept_map, yonetici_map):
    dept_names = list(dept_map.values())
    yonetici_names = ["- Yok -"] + list(yonetici_map.values())
    seviye_list = [f"{k} - {v['name']}" for k,v in sorted(POSITION_LEVELS.items())]

    return st.data_editor(
        df, num_rows="dynamic", width="stretch", key="editor_personel_main_ui",
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
        clear_personnel_cache()
        st.session_state['_personel_flash'] = "✅ Personel listesi başarıyla güncellendi!"
        st.rerun()
    except Exception as e: st.error(f"Hata: {e}")

def _update_single_personel(conn, row):
    p_id = int(row['id'])
    p_rol = normalize_role_string(_rol_seviyeden_belirle(row['pozisyon_seviye']))
    p_dept_name = str(row['departman_adi']).replace(".. ", "").replace("↳ ", "").strip()

    sql = text("""UPDATE personel SET ad_soyad=:a, qms_departman_id=:d, departman_id=:d, bolum=:bn, yonetici_id=:y, pozisyon_seviye=:ps, rol=:r, gorev=:g, durum=:st, ise_giris_tarihi=:ig, servis_duragi=:sd, telefon_no=:tn, operasyonel_bolum_id=:ob, ikincil_yonetici_id=:iy, ayrilma_tarihi=:at, ayrilma_nedeni=:an, guncelleme_tarihi=CURRENT_TIMESTAMP WHERE id=:id""")
    update_params = {
        "a":row['ad_soyad'], "d": robust_id_clean(row['departman_id']),
        "bn":p_dept_name, "y": robust_id_clean(row['yonetici_id']),
        "ps":row['pozisyon_seviye'], "r":p_rol, "g":row['gorev'], "st":row['durum'],
        "ig":str(row['ise_giris_tarihi']), "sd":row['servis_duragi'], "tn":row['telefon_no'],
        "ob": robust_id_clean(row['operasyonel_bolum_id']),
        "iy": robust_id_clean(row['ikincil_yonetici_id']), "id":p_id,
        "at": row.get('ayrilma_tarihi'), "an": row.get('ayrilma_nedeni')
    }
    conn.execute(sql, update_params)

    # MADDE 2.1: %100 Dinamik Senkronizasyon
    sync_data = {k: v for k, v in update_params.items() if k != 'id'}
    sync_personnel_to_users(conn, p_id, sync_data)
def _bagimliliklari_kontrol(engine, personel_id):
    """Silinecek personelin bağımlı kayıt sayılarını döner."""
    tablolar = {
        'personel_vardiya_programi': 'Vardiya Programı',
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
        # v6.8.9: Atomic Double Delete - Cleans both tables to ensure integrity
        conn.execute(text("DELETE FROM ayarlar_kullanicilar WHERE id=:p"), {"p": personel_id})
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
        # v6.8.9: Targeted Source - Delete list now includes ALL personnel, not just users
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
            f'Onaylamak için **"{p_adi}"** yazın', key=f"sil_onay_{p_id}"
        )
        if st.button("🗑️ Kalıcı Olarak Sil", type="primary", key=f"sil_btn_{p_id}"):
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
        try:
            # v6.8.9: Link User to Personnel via 'personel' table source
            fabrika_personel_df = run_query("SELECT p.*, COALESCE(d.ad, 'Tanımsız') as bolum_adi_display FROM personel p LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id ORDER BY p.ad_soyad")
        except Exception as e:
            st.error(f"Personel verisi yüklenirken hata: {e}")
            fabrika_personel_df = None

        if fabrika_personel_df is not None and not fabrika_personel_df.empty:
            # v7.0.1: Handle NULL ad_soyad safely
            fabrika_personel_df['display_name'] = (fabrika_personel_df['ad_soyad'].fillna('Bilinmiyor') +
                                                    " (" + fabrika_personel_df['bolum_adi_display'].astype(str) + ")")
            personel_dict = dict(zip(fabrika_personel_df['id'], fabrika_personel_df['display_name']))

            # v7.0.2 FIX: Add key and index=0 to prevent IndexError on refresh
            secilen_personel_id = st.selectbox("👤 Personel Seçin", options=fabrika_personel_df['id'].tolist(),
                                                index=0, key="new_user_personel_sec",
                                                format_func=lambda x: personel_dict.get(x, f"ID: {x}"))
            secilen_row = fabrika_personel_df[fabrika_personel_df['id'] == secilen_personel_id].iloc[0]

            _v = st.session_state.get('_fv_new_user_form_ui', 0)
            with st.form(f"new_user_form_ui_v{_v}"):
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

                            # v7.0.2 FIX: Check if user exists, INSERT if not, UPDATE if exists
                            existing = conn.execute(text("SELECT id FROM ayarlar_kullanicilar WHERE id=:pid"), {"pid": int(secilen_personel_id)}).fetchone()

                            if existing:
                                # User exists: UPDATE
                                conn.execute(text("UPDATE ayarlar_kullanicilar SET kullanici_adi=:k, sifre=:s, rol=:r, durum='AKTİF' WHERE id=:pid"),
                                           {"k":n_user, "s":hashed_pass, "r":fixed_rol, "pid":int(secilen_personel_id)})
                            else:
                                # User doesn't exist: INSERT with personnel data
                                pers_data = secilen_row
                                conn.execute(text("""INSERT INTO ayarlar_kullanicilar (id, ad_soyad, kullanici_adi, sifre, rol, durum)
                                                     VALUES (:id, :ad, :k, :s, :r, 'AKTİF')"""),
                                           {"id": int(secilen_personel_id), "ad": pers_data['ad_soyad'], "k": n_user, "s": hashed_pass, "r": fixed_rol})

                            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('KULLANICI_YETKILENDIRME', :d)"),
                                       {"d": f"Personel (ID: {int(secilen_personel_id)}) yetkilendirildi. Rol: {fixed_rol}"})
                        st.session_state['_fv_new_user_form_ui'] = _v + 1
                        clear_personnel_cache()
                        st.session_state['_personel_flash'] = "✅ Kullanıcı başarıyla yetkilendirildi!"
                        st.rerun()
                    except Exception as e: st.error(f"Hata: {e}")
        else:
            st.info("Sisteme eklenecek personel bulunamadı. Önce Personel Listesine personel ekleyin.")

    st.divider()
    # Mevcut Kullanıcı Listesi Editörü (Yetki dahilinde)
    if kullanici_yetkisi_var_mi("Ayarlar", "Yönet"):
        # VAKA-025: Şifre asla seçilmez, sadece hash durumu kontrolü yapılır (SQL Seviyesinde)
        users_df = run_query("""
            SELECT id, kullanici_adi, rol, ad_soyad, durum,
            CASE WHEN (sifre LIKE '$2b$%' OR sifre LIKE '$2a$%') THEN '✅ Güvenli (Hash)' ELSE '⚠️ Düz Metin' END as sifre_durumu
            FROM ayarlar_kullanicilar WHERE kullanici_adi IS NOT NULL
        """)

        edited_users = st.data_editor(
            users_df, width="stretch", hide_index=True,
            column_config={
                "id": None, 
                "kullanici_adi": st.column_config.TextColumn("🔑 Kullanıcı Adı", disabled=True),
                "ad_soyad": st.column_config.TextColumn("Ad Soyad", disabled=True),
                "sifre_durumu": st.column_config.TextColumn("🔒 Şifre Durumu", disabled=True, width="medium")
            }
        )
        if st.button("💾 Kullanıcıları Güncelle"):
            try:
                with engine.begin() as conn:
                    for _, row in edited_users.iterrows():
                        fixed_rol = normalize_role_string(row['rol'])
                        conn.execute(text("UPDATE ayarlar_kullanicilar SET kullanici_adi=:k, rol=:r, durum=:d, guncelleme_tarihi=CURRENT_TIMESTAMP WHERE id=:id"),
                                     {"k": row['kullanici_adi'], "r": fixed_rol, "d": row['durum'], "id": int(row['id'])})
                    conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('KULLANICI_TOPLU_GUNCELLE', 'Kullanıcı yetkileri güncellendi.')"))
                clear_personnel_cache()
                st.session_state['_personel_flash'] = "✅ Kullanıcı yetkileri başarıyla güncellendi!"
                st.rerun()
            except Exception as e: st.error(f"Hata: {e}")

        st.divider()
        with st.expander("🔑 Şifre Sıfırla"):
            sifre_df = run_query("SELECT id, ad_soyad FROM ayarlar_kullanicilar WHERE kullanici_adi IS NOT NULL ORDER BY ad_soyad")
            if not sifre_df.empty:
                s_id = st.selectbox("Kullanıcı", sifre_df['id'].tolist(),
                                    format_func=lambda x: sifre_df[sifre_df['id'] == x]['ad_soyad'].values[0],
                                    key="sifre_sifirla_sel")
                yeni_sifre = st.text_input("Yeni Şifre", type="password", max_chars=64, key="yeni_sifre_input")
                if st.button("🔒 Şifreyi Güncelle", key="sifre_guncelle_btn"):
                    if not yeni_sifre:
                        st.warning("Şifre boş olamaz.")
                    else:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("UPDATE ayarlar_kullanicilar SET sifre=:s WHERE id=:id"),
                                             {"s": sifre_hashle(yeni_sifre), "id": int(s_id)})
                                conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('SIFRE_GUNCELLE', :d)"),
                                             {"d": f"Kullanici ID:{s_id} sifresi guncellendi."})
                            clear_personnel_cache()
                            st.session_state['_personel_flash'] = "✅ Şifre başarıyla güncellendi!"
                            st.rerun()
                        except Exception as e: st.error(f"Hata: {e}")
