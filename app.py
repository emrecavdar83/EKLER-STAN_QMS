# Ekleristan QMS - V: 4.0.7.4 - ZONE ARCHITECTURE & LIVE-SYNC READY
# v4.0.3 - Data Consistency & UI Fixes
import streamlit as st
import os

# v4.1.2-STABILIZE: MUST BE FIRST CALL
st.set_page_config(
    page_title="Ekleristan QMS",
    page_icon="https://www.ekleristan.com/wp-content/uploads/2024/02/EKLERISTAN-02-150x150.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

from logic.branding import set_branding, render_corporate_header
set_branding()   # v4.1.2: Perform CSS injection ONLY
from static.logo_b64 import LOGO_B64

# --- v5.8.9: FORCED PERFORMANCE SCHEMA & CACHE RESET ---
if not os.path.exists("tmp/cloud_force_v589.lock"):
    try:
        from sqlalchemy import create_engine, text
        db_url = st.secrets["DB_URL"] if "DB_URL" in st.secrets else (st.secrets["streamlit"]["DB_URL"] if "streamlit" in st.secrets else None)
        if db_url:
            f_engine = create_engine(db_url)
            with f_engine.begin() as conn:
                # 1. Performans Tablosu (Zorunlu)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS performans_degerledirme (
                        id SERIAL PRIMARY KEY,
                        uuid TEXT UNIQUE,
                        personel_id INTEGER,
                        calisan_adi_soyadi TEXT,
                        bolum TEXT,
                        gorevi TEXT,
                        ise_giris_tarihi DATE,
                        donem TEXT,
                        degerlendirme_tarihi DATE,
                        degerlendirme_yili INTEGER,
                        kkd_kullanimi INTEGER DEFAULT 0,
                        mesleki_kriter_2 INTEGER DEFAULT 0,
                        mesleki_kriter_3 INTEGER DEFAULT 0,
                        mesleki_kriter_4 INTEGER DEFAULT 0,
                        mesleki_kriter_5 INTEGER DEFAULT 0,
                        mesleki_kriter_6 INTEGER DEFAULT 0,
                        mesleki_kriter_7 INTEGER DEFAULT 0,
                        mesleki_kriter_8 INTEGER DEFAULT 0,
                        mesleki_ortalama_puan FLOAT DEFAULT 0.0,
                        calisma_saatleri_uyum INTEGER DEFAULT 0,
                        ogrenme_kabiliyeti INTEGER DEFAULT 0,
                        iletisim_becerisi INTEGER DEFAULT 0,
                        problem_cozme INTEGER DEFAULT 0,
                        kalite_bilinci INTEGER DEFAULT 0,
                        ise_baglilik_aidiyet INTEGER DEFAULT 0,
                        ekip_calismasi_uyum INTEGER DEFAULT 0,
                        verimli_calisma INTEGER DEFAULT 0,
                        kurumsal_ortalama_puan FLOAT DEFAULT 0.0,
                        agirlikli_toplam_puan FLOAT DEFAULT 0.0,
                        polivalans_duzeyi TEXT,
                        polivalans_kodu TEXT,
                        yorum TEXT,
                        degerlendiren_adi TEXT,
                        guncelleyen_kullanici TEXT,
                        surum INTEGER DEFAULT 1,
                        onceki_puan FLOAT DEFAULT 0.0,
                        sync_durumu TEXT DEFAULT 'senkronize',
                        silinmis INTEGER DEFAULT 0,
                        olusturma_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # 2. Yetki Önbelleğini Zorla Temizle (Force Reset)
                if 'batch_yetki_map' in st.session_state:
                    del st.session_state['batch_yetki_map']
                st.cache_data.clear()
                
                conn.execute(text("INSERT INTO sistem_loglari (ajan_adi, islem_kodu, detaylar) VALUES ('Antigravity', 'v5.8.9_FORCE', 'Performance Schema & Cache Reset')"))

            if not os.path.exists("tmp"): os.makedirs("tmp")
            with open("tmp/cloud_force_v589.lock", "w") as f: f.write("v589_applied")
    except Exception as e:
        print(f"v5.8.9 Force Sync Warning: {e}")

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import pytz
import os
import extra_streamlit_components as cookie_manager

def get_cookie_manager():
    # v5.7.7: Removed @st.cache_resource as widgets cannot be cached.
    # Singleton pattern: cookie_manager_obj is created once globally.
    return cookie_manager.CookieManager(key="qms_cookie_manager")

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
    audit_log_kaydet
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
st.sidebar.caption("v4.3.3-FINAL - Güvenli Hashing & Sessiz Bakım 🛡️")
st.markdown("""
<style>
div.stButton > button:first-child {background-color: #8B0000; color: white; width: 100%; border-radius: 5px;}
.stRadio > label {font-weight: bold;}
@media (min-width: 1024px) {
    [data-testid="stHeaderActionElements"], .stAppDeployButton, [data-testid="stManageAppButton"], 
    [data-testid="stDecoration"], footer { display: none !important; }
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
        import time; time.sleep(0.5)
    except: pass
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
        # v4.1.4: Lazy Load Cookie Manager
        cookie_manager_obj = get_cookie_manager()
        remember_token = cookie_manager_obj.get("qms_remember_me")
        if remember_token:
            from logic.auth_logic import kalici_oturum_dogrula
            from streamlit.web.server.websocket_headers import _get_websocket_headers
            u_data = kalici_oturum_dogrula(engine, remember_token, cihaz_bilgisi=_get_websocket_headers().get("User-Agent", "Bilinmiyor"))
            if u_data:
                from logic.zone_yetki import yetki_haritasi_yukle
                st.session_state.logged_in = True
                st.session_state.user = u_data.get('kullanici_adi')
                st.session_state.user_rol = u_data.get('rol', 'Personel')
                st.session_state.user_fullname = str(u_data.get('ad_soyad', st.session_state.user)).strip().upper()
                
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
        with engine.connect() as conn:
            p_df = pd.read_sql(text("SELECT id, ad_soyad, kullanici_adi, sifre, rol, durum, departman_id FROM personel WHERE durum='AKTİF' OR kullanici_adi='Admin'"), conn)
            p_df.columns = [c.lower().strip() for c in p_df.columns]
        users = p_df['kullanici_adi'].dropna().unique().tolist() if not p_df.empty else ["Admin"]
        user = st.selectbox("Kullanıcı Seçiniz", users)
        pwd = st.text_input("Şifre", type="password")
        remember_me = st.checkbox("Beni Hatırla (7 Gün)", value=True)
        if st.button("Giriş Yap", use_container_width=True):
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
                            st.session_state.active_module_key = "portal"
                            yetki_haritasi_yukle(engine, st.session_state.user_rol)
                            audit_log_kaydet("OTURUM_ACILDI", f"{user} giriş yaptı.")
                            if remember_me:
                                from logic.auth_logic import kalici_oturum_olustur
                                from streamlit.web.server.websocket_headers import _get_websocket_headers
                                # v5.8.0: Başlangıç modülü (portal) ile oturum oluştur
                                token = kalici_oturum_olustur(engine, int(u_data.iloc[0]['id']), 
                                                              _get_websocket_headers().get("User-Agent", "Bilinmiyor"),
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
    
    # v4.1.3: DuplicateWidgetID (I6Q2) Zırhı - Listeyi her zaman tekilleştir
    modul_listesi = list(dict.fromkeys(modul_listesi))
    st.session_state.available_modules = modul_listesi

    # --- v4.3.6: P0 NAVIGATION UNLOCK (State Liberation) ---
    # Widget'ları session_state ile zorlamak yerine index parametresi ile kontrol ediyoruz.
    if 'active_module_key' not in st.session_state:
        st.session_state.active_module_key = "portal"
    
    # Master Label'ı ve onun liste içindeki sırasını (index) bul
    selected_label = SLUG_TO_LABEL.get(st.session_state.active_module_key, modul_listesi[0])
    try:
        active_index = modul_listesi.index(selected_label)
    except:
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
            if st.button("🏠 Ana Sayfa", use_container_width=True, key="global_home_btn"):
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
            if st.button("🚪", help="Sistemden Güvenli Çıkış (Logout)", key="top_logout_btn", use_container_width=True):
                guvenli_cikis_yap()

    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    with st.sidebar:
        st.image(LOGO_B64)
        st.write(f"👤 **{st.session_state.get('user', 'Misafir')}**")
        if st.button("🚪 Sistemi Kapat (Logout)", use_container_width=True, key="logout_btn"):
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

    # --- MODÜL DİSPATCHER (v4.0.7.4 SAFE) ---
    try:
        # DB'den veya fallback'ten gelen anahtarı standartlaştır
        m_key = str(st.session_state.active_module_key).lower().strip()
        def zone_gate(z):
            if not zone_girebilir_mi(z): st.error("🚫 Yetki Yok"); st.stop()

        if m_key == "portal":
            from ui.portal.portal_ui import render_portal_module
            render_portal_module(engine)
        elif m_key == "uretim_girisi":
            zone_gate('ops'); from ui.uretim_ui import render_uretim_module
            render_uretim_module(engine, guvenli_kayit_ekle)
        elif m_key == "qdms":
            zone_gate('mgt'); from ui.qdms_ui import qdms_main_page
            qdms_main_page(engine)
        elif m_key == "kpi_kontrol":
            zone_gate('mgt'); from ui.kpi_ui import render_kpi_module
            render_kpi_module(engine, guvenli_kayit_ekle)
        elif m_key == "gmp_denetimi":
            zone_gate('mgt'); from ui.gmp_ui import render_gmp_module
            render_gmp_module(engine)
        elif m_key == "personel_hijyen":
            from ui.hijyen_ui import render_hijyen_module
            render_hijyen_module(engine, guvenli_coklu_kayit_ekle)
        elif m_key == "temizlik_kontrol":
            from ui.temizlik_ui import render_temizlik_module
            render_temizlik_module(engine)
        elif m_key == "kurumsal_raporlama":
            zone_gate('mgt'); from ui.raporlama_ui import render_raporlama_module
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
            zone_gate('mgt'); from ui.performans.performans_sayfasi import performans_sayfasi_goster
            performans_sayfasi_goster()
        elif m_key == "ayarlar":
            zone_gate('sys'); from ui.ayarlar.ayarlar_orchestrator import render_ayarlar_orchestrator
            render_ayarlar_orchestrator(engine)
        elif m_key == "profilim":
            from ui.profil_ui import render_profil_modulu
            render_profil_modulu(engine)
    except Exception as e:
        # v4.3.3-FINAL: Streamlit'in içsel akış kontrolü (Rerun, Stop, SwitchPage) hata DEĞİLDİR.
        # Bunları hata sistemine sokmadan doğrudan Streamlit'e iade etmeliyiz.
        e_type = type(e).__name__
        if e_type in ["StopException", "RerunException", "SwitchPageException", "TriggerRerun"]:
            raise e
        
        # Gerçek teknik hatalar burada yakalanır
        from logic.error_handler import handle_exception
        handle_exception(e, modul="APP_DISPATCHER", tip="UI")

if __name__ == "__main__":
    if st.session_state.get('logged_in'): main_app()
    else: login_screen()

if st.sidebar.button("🧹 Reset", use_container_width=True):
    clear_all_cache(); st.session_state.clear(); st.rerun()
