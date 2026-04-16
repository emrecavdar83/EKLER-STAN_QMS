# Ekleristan QMS - V: 6.1.0 - Stabilization & Technical Debt Cleanup
# v4.7.0 - Forced schema initialization & Personel Status fix
import streamlit as st
import os

# v4.1.2-STABILIZE: MUST BE FIRST CALL
st.set_page_config(
    page_title="Ekleristan QMS",
    page_icon="https://www.ekleristan.com/wp-content/uploads/2024/02/EKLERISTAN-02-150x150.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 0. FORCE MIGRATION (ANAYASA v6.3.3) ---
# v4.7.0: Her açılışta şema senkronizasyonunu en başta zorla.
try:
    from database.connection import get_engine
    get_engine()
except Exception as e:
    st.error(f"CRITICAL_MIGRATION_FAIL: {e}")
    st.session_state.migration_error = str(e)

# v6.3.9: DB Tanılama — yalnızca oturum açmış ADMIN kullanıcılara gösterilir
if (st.session_state.get('logged_in') and
        str(st.session_state.get('user_rol', '')).upper() == 'ADMIN'):
    if st.sidebar.checkbox("🔧 DB Tanılama (Admin)", key="db_diag_cb"):
        try:
            from sqlalchemy import text as _sql_text
            _eng = get_engine()
            with _eng.connect() as _conn:
                _res = _conn.execute(_sql_text(
                    "SELECT current_schema(), current_database()"
                )).fetchone()
                st.sidebar.caption(f"Schema: `{_res[0]}` | DB: `{_res[1]}`")
        except Exception as _diag_e:
            st.sidebar.error(f"Tanılama hatası: {_diag_e}")

from logic.branding import set_branding, render_corporate_header
set_branding()   # v4.1.2: Perform CSS injection ONLY
from static.logo_b64 import LOGO_B64


import pandas as pd
from sqlalchemy import create_engine, text
# v6.3.3: GLOBAL PANDAS/SQLAlchemy FIX (Removed Stage 1 - C1)
import pandas as pd
from sqlalchemy import create_engine, text

from datetime import datetime, timedelta
import time
import pytz
import os
import extra_streamlit_components as cookie_manager

def get_cookie_manager():
    # v5.8.1: Singleton Pattern using session_state to prevent DuplicateKeyError
    if "cookie_manager_instance" not in st.session_state:
        st.session_state.cookie_manager_instance = cookie_manager.CookieManager(key="qms_cookie_manager")
    return st.session_state.cookie_manager_instance

# v4.1.4: Global initialization (Singleton for v5.7.7 Stabilization)
cookie_manager_obj = get_cookie_manager()


from constants import (
    POSITION_LEVELS,
    MANAGEMENT_LEVELS,
    STAFF_LEVELS,
    get_position_name,
    get_position_icon,
    get_position_color,
    get_position_label,
    VARDIYA_LISTESI
)


from logic.data_fetcher import (
    run_query, get_user_roles, get_department_tree,
    get_department_options_hierarchical,
    get_all_sub_department_ids, get_personnel_hierarchy,
    cached_veri_getir, veri_getir,
    get_personnel_shift, is_personnel_off
)

from logic.auth_logic import (
    sistem_modullerini_getir,
    kullanici_yetkisi_getir_dinamik,
    kullanici_yetkisi_var_mi,
    sifre_dogrula,
    audit_log_kaydet,
    MODUL_ESLEME
)


from logic.cache_manager import (
    clear_personnel_cache,
    clear_department_cache,
    clear_all_cache
)

# --- 1. AYARLAR & VERİTABANI BAĞLANTISI ---
from database.connection import get_engine
engine = get_engine()

# --- PRE-FLIGHT ZONE ---
from logic.zone_yetki import (
    yetki_haritasi_yukle,
    zone_girebilir_mi,
    modul_gorebilir_mi,
    eylem_yapabilir_mi,
    varsayilan_modul_getir,
    sorgu_sayisini_getir
)

giris_var = st.session_state.get('logged_in', False)

if giris_var and 'yetki_haritasi' not in st.session_state:
    st.session_state.yetki_haritasi = yetki_haritasi_yukle(
        engine,
        st.session_state.get('user_rol', 'Personel')
    )

if giris_var and 'active_module_key' not in st.session_state:
    st.session_state.active_module_key = varsayilan_modul_getir()

ADMIN_USERS, CONTROLLER_ROLES = get_user_roles()

def get_istanbul_time():
    now = datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)

# --- 2. CSS & TEMA ---
st.sidebar.title("Ekleristan QMS")
st.sidebar.caption("v6.1.0-STABLE")
st.markdown("""
<style>
div.stButton > button:first-child {background-color: #8B0000; color: white; width: 100%; border-radius: 5px;}
.stRadio > label {font-weight: bold;}
@media (min-width: 1024px) {
    [data-testid="stHeaderActionElements"], .stAppDeployButton, [data-testid="stManageAppButton"], 
    [data-testid="stDecoration"], footer { display: none !important; }
}

/* v4.7.1: Dropdown (Selectbox) Z-Index Zırhı 
Hızlı menü açıldığında alttaki butonların üzerine binme (overlapping) sorununu çözer */
div[data-baseweb="popover"], div[role="listbox"] {
    z-index: 9999999 !important;
}
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = ""

# --- 2.5: GÜVENLİ TAHLİYE ZIRHI (v5.1.1) ---
# Eğer URL'de logout parametresi varsa veya logging_out flag'i set edildiyse
if st.query_params.get("logout") == "1":
    try:
        cm = get_cookie_manager()
        cm.delete("qms_remember_me")
        # Kısa bir bekleme tarayıcının işlemi bitirmesi için (Opsiyonel)
    except Exception:
        pass
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

# --- 3. QR & KALICI OTURUM ---
if "scanned_qr" in st.query_params:
    _qr_val = st.query_params.get('scanned_qr', '').strip()
    if _qr_val:
        st.session_state.active_module_name = "❄️ Soğuk Oda Sıcaklıkları"
        st.session_state.scanned_qr_code = _qr_val
        if not st.session_state.get('logged_in'):
            st.session_state.logged_in = True
            st.session_state.user = "Saha_Mobil"
            st.session_state.user_rol = "Personel"

# Sadece logout modunda değilsek 'Beni Hatırla' kontrolü yap
if not st.session_state.get('logged_in') and st.query_params.get("logout") != "1":
    try:
        # v5.8.1: Using centralized cookie manager singleton
        remember_token = get_cookie_manager().get("qms_remember_me")
        if remember_token:
            from logic.auth_logic import kalici_oturum_dogrula
            u_data = kalici_oturum_dogrula(engine, remember_token, cihaz_bilgisi=st.context.headers.get("User-Agent", "Bilinmiyor"))
            if u_data:
                from logic.zone_yetki import yetki_haritasi_yukle
                st.session_state.logged_in = True
                st.session_state.user = u_data.get('kullanici_adi')
                st.session_state.user_rol = u_data.get('rol', 'Personel')
                st.session_state.user_fullname = str(u_data.get('ad_soyad', st.session_state.user)).strip().upper()
                st.session_state.user_id = int(u_data.get('id', 0))
                
                # v5.8.0: Modül Hafızası Yükleme
                saved_module = u_data.get('son_modul', 'portal')
                st.session_state.active_module_key = saved_module
                
                yetki_haritasi_yukle(engine, st.session_state.user_rol)
                st.rerun()
    except: pass

def login_screen():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image(LOGO_B64, width=200)
        st.title("🔐 EKLERİSTAN QMS")
        # v6.3.2: Manual Fetch Bypass (Pandas 3.13 / SQLAlchemy 2.0.x TypeError Fix)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT id, ad_soyad, kullanici_adi, sifre, rol, durum, departman_id FROM personel WHERE durum='AKTİF' OR kullanici_adi='Admin'"))
            p_df = pd.DataFrame(res.fetchall(), columns=res.keys())
        p_df.columns = [c.lower().strip() for c in p_df.columns]
        users = p_df['kullanici_adi'].dropna().unique().tolist() if not p_df.empty else ["Admin"]
        user = st.selectbox("Kullanıcı Seçiniz", users)
        pwd = st.text_input("Şifre", type="password")
        remember_me = st.checkbox("Beni Hatırla (7 Gün)", value=True)
        if st.button("Giriş Yap", width="stretch"):
            if not p_df.empty:
                u_data = p_df[p_df['kullanici_adi'].astype(str) == str(user)]
                if not u_data.empty:
                    db_pass = str(u_data.iloc[0]['sifre']).strip().removesuffix(".0")
                    if sifre_dogrula(str(pwd).strip(), db_pass, user):
                        if str(u_data.iloc[0].get('durum')).upper() not in ['AKTİF', 'TRUE']:
                            st.error("⛔ Hesabınız PASİF durumdadır.")
                        else:
                            from logic.zone_yetki import yetki_haritasi_yukle
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.session_state.user_rol = u_data.iloc[0].get('rol', 'Personel')
                            st.session_state.user_fullname = str(u_data.iloc[0].get('ad_soyad', user)).strip().upper()
                            st.session_state.user_id = int(u_data.iloc[0]['id'])
                            st.session_state.user_dept_id = int(u_data.iloc[0]['departman_id']) if not pd.isna(u_data.iloc[0]['departman_id']) else None
                            st.session_state.active_module_key = "portal"
                            yetki_haritasi_yukle(engine, st.session_state.user_rol)
                            audit_log_kaydet("OTURUM_ACILDI", f"{user} giriş yaptı.")
                            if remember_me:
                                from logic.auth_logic import kalici_oturum_olustur
                                # v5.8.0: Başlangıç modülü (portal) ile oturum oluştur
                                token = kalici_oturum_olustur(engine, int(u_data.iloc[0]['id']), 
                                                              st.context.headers.get("User-Agent", "Bilinmiyor"),
                                                              son_modul=st.session_state.get('active_module_key', 'portal'))
                                # v4.1.4: Using global cookie_manager_obj (Singleton)
                                cookie_manager_obj.set("qms_remember_me", token, expires_at=datetime.now() + timedelta(days=7))
                            st.rerun()
                    else: st.error("❌ Hatalı Şifre!")
                else: st.error("❓ Kullanıcı bulunamadı.")

# --- 4. ANA UYGULAMA ---
def main_app():
    from logic.db_writer import guvenli_kayit_ekle, guvenli_coklu_kayit_ekle
    # v4.2.0: IMMUTABLE STARTUP (Mutation Fix)
    # Önbellekteki orijinal listeyi bozmamak için (6L6T) yeni bir liste oluşturuyoruz.
    RAW_MODULE_PAIRS = [("🏠 Portal (Ana Sayfa)", "portal")] + list(sistem_modullerini_getir())
    
    SLUG_TO_LABEL = {m[1]: m[0] for m in RAW_MODULE_PAIRS}
    LABEL_TO_SLUG = {m[0]: m[1] for m in RAW_MODULE_PAIRS}
    SLUG_TO_LABEL["profilim"] = "👤 Profilim"; LABEL_TO_SLUG["👤 Profilim"] = "profilim"

    # v4.1.8: ADMIN (GOD MODE) VISIBILITY FIX
    u_rol = str(st.session_state.get('user_rol', 'MISAFIR')).upper()
    modul_listesi = [m[0] for m in RAW_MODULE_PAIRS if m[1] == 'portal' or u_rol == 'ADMIN' or modul_gorebilir_mi(m[1])]
    if "👤 Profilim" not in modul_listesi: modul_listesi.append("👤 Profilim")
    
    # v5.8.14: Slug-based Unique Protection
    seen_slugs = set()
    final_modul_listesi = []
    for label in modul_listesi:
        slug = LABEL_TO_SLUG.get(label)
        if slug not in seen_slugs:
            final_modul_listesi.append(label)
            seen_slugs.add(slug)
    
    modul_listesi = final_modul_listesi
    st.session_state.available_modules = modul_listesi

    # --- v4.3.6: P0 NAVIGATION UNLOCK (State Liberation) ---
    # Widget'ları session_state ile zorlamak yerine index parametresi ile kontrol ediyoruz.
    if 'active_module_key' not in st.session_state:
        st.session_state.active_module_key = "portal"
    
    # Master Label'ı ve onun liste içindeki sırasını (index) bul
    selected_label = SLUG_TO_LABEL.get(st.session_state.active_module_key, modul_listesi[0])
    try:
        active_index = modul_listesi.index(selected_label)
    except Exception:
        active_index = 0

    # --- v4.1.0: PREMIUM CORPORATE HEADER ---
    render_corporate_header()

    # --- ÜST HIZLI MENÜ HEADER (Dinamik Bilgi Barı) ---
    # v5.1.1: HARDENED LOGOUT (Zırhlı Tahliye v2.0)
    def guvenli_cikis_yap():
        """Beni Hatırla döngüsünü kıran ve tüm oturum izlerini silen tahliye fonksiyonu."""
        try:
            # 1. Cookie Manager'ı hazırla
            cm = get_cookie_manager()
            token = cm.get("qms_remember_me")
            if token:
                from logic.auth_logic import kalici_oturum_sil
                kalici_oturum_sil(engine, token)
        except: pass
        
        # 2. Öncelikli Tahliye Parametresi (v5.1.1)
        st.query_params["logout"] = "1"
        st.session_state.logged_in = False
        st.rerun()

    c1, mid, c2 = st.columns([1, 2, 1])
    with c1:
        # v5.1.2: Safe Get Zırhı (AttributeError Fix)
        if st.session_state.get('active_module_key', 'portal') != "portal":
            if st.button("🏠 Ana Sayfa", width="stretch", key="global_home_btn"):
                st.session_state.active_module_key = "portal"
                # v5.8.0: Veritabanında oturumu güncelle
                try:
                    token = get_cookie_manager().get("qms_remember_me")
                    if token:
                        from logic.auth_logic import oturum_modul_guncelle
                        oturum_modul_guncelle(engine, token, "portal")
                except: pass
                st.rerun()
    with mid:
        # Yol bilgisi (Estetik & Senkronize)
        st.markdown(f"""
            <div style="text-align: center; color: #64748b; font-size: 0.9rem; padding-top: 5px;">
                <span style="font-weight: 600;">Modül:</span> {selected_label}
            </div>
        """, unsafe_allow_html=True)
    with c2:
        def sync_from_quick():
            try:
                label = st.session_state.get('quick_nav')
                slug = LABEL_TO_SLUG.get(label)
                # v5.1.2: Safe Access Check
                current_active = st.session_state.get('active_module_key', 'portal')
                if slug and current_active != slug:
                    st.session_state.active_module_key = slug
                    # v5.8.0: Veritabanında oturumu güncelle
                    try:
                        token = get_cookie_manager().get("qms_remember_me")
                        if token:
                            from logic.auth_logic import oturum_modul_guncelle
                            oturum_modul_guncelle(engine, token, slug)
                    except: pass
                    st.rerun()
            except: pass
        
        # v4.4.5: Sağ Üst Hızlı Menü ve Çıkış Yan Yana
        c2_1, c2_2 = st.columns([3, 1])
        with c2_1:
            st.selectbox("🚀 HIZLI", modul_listesi, index=active_index, key="quick_nav", label_visibility="collapsed", on_change=sync_from_quick)
        with c2_2:
            # v5.1.0: Zırhlı Çıkış butonu
            if st.button("🚪", help="Sistemden Güvenli Çıkış (Logout)", key="top_logout_btn", width="stretch"):
                guvenli_cikis_yap()

    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    with st.sidebar:
        st.image(LOGO_B64)
        st.write(f"👤 **{st.session_state.get('user', 'Misafir')}**")
        if st.button("🚪 Sistemi Kapat (Logout)", width="stretch", key="logout_btn"):
            guvenli_cikis_yap()
        st.markdown("---")
        
        def sync_from_sidebar():
            try:
                label = st.session_state.get('sidebar_nav')
                slug = LABEL_TO_SLUG.get(label)
                # v5.1.2: Safe Access Check (AttributeError Barrier)
                current_active = st.session_state.get('active_module_key', 'portal')
                if slug and current_active != slug:
                    st.session_state.active_module_key = slug
                    # v5.8.0: Veritabanında oturumu güncelle
                    try:
                        token = get_cookie_manager().get("qms_remember_me")
                        if token:
                            from logic.auth_logic import oturum_modul_guncelle
                            oturum_modul_guncelle(engine, token, slug)
                    except: pass
                    st.rerun()
            except: pass

        # Yan menüyü de index-controlled hale getiriyoruz
        st.radio("🏠 ANA MENÜ", modul_listesi, index=active_index, key="sidebar_nav", on_change=sync_from_sidebar)
        if st.session_state.get('user_rol') == 'ADMIN':
            st.caption(f"⚡ Sorgu: {sorgu_sayisini_getir()}")

    # --- MODÜL DİSPATCHER (v6.3.9 SMOOTH TRANSITION) ---
    try:
        raw_key = str(st.session_state.get('active_module_key', 'portal')).strip()
        m_key = MODUL_ESLEME.get(raw_key, raw_key).lower().strip()

        # v6.6.0: Modül geçiş tespiti — widget state izolasyonu
        _prev = st.session_state.get('_prev_module_key', m_key)
        if _prev != m_key:
            # Eski modüle ait geçici widget state'lerini temizle (gölge durum önleme)
            _prefix_map = {
                "portal": "portal_btn_",
                "personel": "sil_onay_",
                "hijyen": ("s_", "a_"),
                "kpi": "kpi_",
                "soguk_oda": "sosts_",
                "ayarlar": ("settings_", "org_", "prod_"),  # v6.2.1: Ayarlar izolasyonu
                "map_uretim": "map_",                       # v6.2.1: MAP izolasyonu
                "qdms": "qdms_",                            # v6.2.1: QDMS izolasyonu
            }
            _old_prefixes = _prefix_map.get(_prev, ())
            if isinstance(_old_prefixes, str):
                _old_prefixes = (_old_prefixes,)
            stale_keys = [k for k in list(st.session_state.keys())
                          if any(k.startswith(p) for p in _old_prefixes)]
            for k in stale_keys:
                del st.session_state[k]
            st.session_state['_prev_module_key'] = m_key

        def zone_gate(z):
            """Bölge yetki kapısı — yetkisiz erişimi engeller."""
            if not zone_girebilir_mi(z):
                st.error(f"🚫 '{z.upper()}' bölgesine erişim yetkiniz bulunmamaktadır.")
                st.stop()

        _module_slot = st.empty()
        with _module_slot.container():
            if m_key == "portal":
                from ui.portal.portal_ui import render_portal_module
                render_portal_module(engine)
            elif m_key == "uretim_girisi":
                zone_gate('ops')
                from ui.uretim_ui import render_uretim_module
                render_uretim_module(engine, guvenli_kayit_ekle)
            elif m_key == "qdms":
                zone_gate('mgt')
                from ui.qdms_ui import qdms_main_page
                qdms_main_page(engine)
            elif m_key == "kpi_kontrol":
                zone_gate('mgt')
                from ui.kpi_ui import render_kpi_module
                render_kpi_module(engine, guvenli_kayit_ekle)
            elif m_key == "gmp_denetimi":
                zone_gate('mgt')
                from ui.gmp_ui import render_gmp_module
                render_gmp_module(engine)
            elif m_key == "personel_hijyen":
                from ui.hijyen_ui import render_hijyen_module
                render_hijyen_module(engine, guvenli_coklu_kayit_ekle)
            elif m_key == "temizlik_kontrol":
                from ui.temizlik_ui import render_temizlik_module
                render_temizlik_module(engine)
            elif m_key == "kurumsal_raporlama":
                zone_gate('mgt')
                from ui.raporlar.dispatcher import render_raporlama_module
                render_raporlama_module(engine)
            elif m_key == "soguk_oda":
                from ui.soguk_oda_ui import render_sosts_module
                render_sosts_module(engine)
            elif m_key == "map_uretim":
                from ui.map_uretim.map_uretim import render_map_module
                render_map_module(engine)
            elif m_key == "gunluk_gorevler":
                from modules.gunluk_gorev.ui import render_gunluk_gorev_modulu
                render_gunluk_gorev_modulu(engine)
            elif m_key == "personel_vardiya_yonetimi":
                from modules.vardiya.ui import render_vardiya_module
                render_vardiya_module(engine)
            elif m_key == "performans_polivalans":
                zone_gate('mgt')
                from ui.performans.performans_sayfasi import performans_sayfasi_goster
                performans_sayfasi_goster()
            elif m_key == "denetim_izi":
                zone_gate('mgt')
                from ui.denetim_izi_ui import render_denetim_izi_module
                render_denetim_izi_module(engine)
            elif m_key == "ayarlar":
                zone_gate('sys')
                from ui.ayarlar.ayarlar_orchestrator import render_ayarlar_orchestrator
                render_ayarlar_orchestrator(engine)
            elif m_key == "profilim":
                from ui.profil_ui import render_profil_modulu
                render_profil_modulu(engine)
    except Exception as e:
        # Streamlit iç akış kontrolü (Rerun, Stop, SwitchPage) hata değildir — yukarı ilet.
        e_type = type(e).__name__
        if e_type in ["StopException", "RerunException", "SwitchPageException", "TriggerRerun"]:
            raise e
        from logic.error_handler import handle_exception
        handle_exception(e, modul="APP_DISPATCHER", tip="UI")

if __name__ == "__main__":
    if st.session_state.get('logged_in'): main_app()
    else: login_screen()

if str(st.session_state.get('user_rol', '')).upper() == 'ADMIN':
    if st.sidebar.button("🧹 Reset (Admin)", width="stretch"):
        clear_all_cache(); st.session_state.clear(); st.rerun()
