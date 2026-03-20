# Ekleristan QMS - V: 3.1.0 - ANTIGRAVITY FIX
# v3.1.5 - Secure UI Core
import streamlit as st
st.set_page_config(page_title="Ekleristan QMS", layout="wide", page_icon="🏭")
from logic.branding import set_branding
from static.logo_b64 import LOGO_B64
set_branding()
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import pytz
import os
import extra_streamlit_components as cookie_manager

def get_cookie_manager():
    return cookie_manager.CookieManager()

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

# UI MODULLERI (MODULAR UI - Lazy Loaded)
# Importlar main_app() içinde ilgili bloklara taşındı (Anayasa Madde 13/Lazy Loading)

# import soguk_oda_utils  <- EKL-PERF-003: Lazy import'a taşındı


# Veritabanı motorunu al
engine = get_engine()

# ── PRE-FLIGHT ZONE ──────────────────────────────────────
from logic.zone_yetki import (
    yetki_haritasi_yukle,
    zone_girebilir_mi,
    modul_gorebilir_mi,
    eylem_yapabilir_mi,
    varsayilan_modul_getir,
)

# 1. Giriş kontrolü çerez bazlı (0 veya 1 DB)
# login_screen zaten app.py içinde tanımlı, if bloğu aşağıda
giris_var = st.session_state.get('logged_in', False)

# 2. Yetki haritası — oturum başında 1 kez yükle
if giris_var and 'yetki_haritasi' not in st.session_state:
    st.session_state.yetki_haritasi = yetki_haritasi_yukle(
        engine,
        st.session_state.get('user_rol', 'Personel')
    )

# 3. Aktif modül — varsayılan veya seçili
if giris_var and 'active_module_key' not in st.session_state:
    st.session_state.active_module_key = varsayilan_modul_getir()

# 🧪 QUANTUM SPEED: Global Bakım (v3.2.0)
# Bakım artık get_engine() içinde @st.cache_resource ile otomatik ve TEK SEFERLİK çalışır.
# app.py seviyesinde manuel çağırmaya gerek kalmadı.



# --- 2. VERİ İŞLEMLERİ ---


ADMIN_USERS, CONTROLLER_ROLES = get_user_roles()

# CACHING: Veri çekme işlemini önbelleğe al (TTL: 60 saniye)
# Böylece her tıklamada tekrar tekrar SQL sorgusu atmaz


# --- YENİ VARDİYA SİSTEMİ YARDIMCI FONKSİYONLARI ---



# Admin listesi get_user_roles() ile cache'den geliyor.
# Geçmişteki try-except bloğu yerine artık merkezi cache devrede.

# Zaman Fonksiyonu
def get_istanbul_time():
    # Atomik Zaman: Milisaniyeleri temizle (.replace(microsecond=0))
    now = datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)

# --- 3. ARAYÜZ BAŞLANGICI ---





# --- 3. ARAYÜZ BAŞLANGICI ---
st.sidebar.title("Ekleristan QMS")
st.sidebar.caption("v3.1.0 - Sistematik Yönetim 🛡️")
st.markdown(
"""
<style>
/* 1. Buton ve Radyo Buton Özelleştirme */
div.stButton > button:first-child {background-color: #8B0000; color: white; width: 100%; border-radius: 5px;}
.stRadio > label {font-weight: bold;}

/* 2. TEMİZ ELLER CSS: Sadece Masaüstünde (Geniş Ekran) Gizle */
@media (min-width: 1024px) {
    [data-testid="stHeaderActionElements"],
    .stAppDeployButton,
    [data-testid="stManageAppButton"],
    [data-testid="stDecoration"],
    footer {
        display: none !important;
    }
}

/* 3. Mobil Header Serbest Bölge: DOKUNMA! */
/* Streamlit'in kendi mobil menüsü (varsa) serbestçe çalışsın. */
</style>
""", unsafe_allow_html=True)

# BOOT CHECK
st.success("✅ SİSTEM ANALİZİ TAMAMLANDI - v3.1.0 AKTİF")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = ""

# --- QR SCAN URL ROUTING (KRİTİK FIX) ---
# Sorun: QR tarayıcı window.parent.location.href ile tam sayfa yenileme yapıyor.
# Bu session_state'i sıfırlıyor. Kullanıcı giriş ekranına düşüyor.
# Çözüm: scanned_qr parametresi varsa kullanıcıyı yeni SOSTS ölçüm sayfasına yönlendir.
if "scanned_qr" in st.query_params:
    _qr_val = st.query_params.get('scanned_qr', '').strip()
    if _qr_val:
        st.session_state.active_module_name = "❄️ Soğuk Oda Sıcaklıkları"
        st.session_state.scanned_qr_code = _qr_val
        if not st.session_state.get('logged_in'):
            st.session_state.logged_in = True
            st.session_state.user = "Saha_Mobil"
            st.session_state.user_rol = "Personel"
            st.session_state.user_bolum = ""

# --- 13. ADAM: KALICI OTURUM KONTROLÜ (REMEMBER ME) ---
if not st.session_state.get('logged_in'):
    try:
        remember_token = cookie_manager_obj.get("qms_remember_me")
        if remember_token:
            from logic.auth_logic import kalici_oturum_dogrula
            from streamlit.web.server.websocket_headers import _get_websocket_headers
            headers = _get_websocket_headers()
            ua = headers.get("User-Agent", "Bilinmiyor")
            
            u_data = kalici_oturum_dogrula(engine, remember_token, cihaz_bilgisi=ua)
            if u_data:
                st.session_state.logged_in = True
                st.session_state.user = u_data.get('kullanici_adi')
                st.session_state.user_rol = u_data.get('rol', 'Personel')
                st.session_state.user_fullname = str(u_data.get('ad_soyad', st.session_state.user)).strip().upper()
                st.session_state.user_bolum = u_data.get('bolum', '') # Varsayım: auth_logic dogrula joinli döner
                # audit_log_kaydet("OTOMATIK_GIRIS", "Kalıcı oturum kullanıldı", st.session_state.user)
                st.rerun()
    except Exception as e:
        pass # Sessiz fail (Anayasa Madde 9: Fail-Silent)

# --- 13. ADAM: HİBRİT NAVİGASYON HUB (ÖLÜMSÜZ MENÜ) ---
# Hamburger menü krizini kökten çözer.
if st.session_state.logged_in:
    # Sayfanın en tepesine, sidebar'dan bağımsız menü koyuyoruz.

    # Modül Listesi (Dinamik & Yetki Bazlı)
    RAW_MODULE_PAIRS = sistem_modullerini_getir() # [(label, key), ...]
    # Yetki kontrolü için artık doğrudan ANAHTAR (slug) kullanıyoruz (S2-D Optimal)
    NAV_MODULES = [m for m in RAW_MODULE_PAIRS if kullanici_yetkisi_var_mi(m[1], gereken_yetki="Görüntüle", audit_log=False)]
    
    if not any(m[1] == "profilim" for m in NAV_MODULES):
        NAV_MODULES.append(("👤 Profilim", "profilim"))

    # Labels and Keys mapping
    NAV_LABELS = [m[0] for m in NAV_MODULES]
    LABEL_TO_KEY = {m[0]: m[1] for m in NAV_MODULES}

    # State tabanlı navigasyon (anahtar bazlı)
    if 'active_module_key' not in st.session_state or st.session_state.active_module_key not in [m[1] for m in NAV_MODULES]:
        st.session_state.active_module_key = NAV_MODULES[0][1]

    # Üst Menü
    current_label = [m[0] for m in NAV_MODULES if m[1] == st.session_state.active_module_key]
    current_label = current_label[0] if current_label else NAV_LABELS[0]

    secim_ust = st.selectbox(
        "📍 HIZLI MENÜ (MODÜL SEÇİNİZ):",
        NAV_LABELS,
        index=NAV_LABELS.index(current_label) if current_label in NAV_LABELS else 0
    )

    # Seçimi kaydet
    st.session_state.active_module_key = LABEL_TO_KEY.get(secim_ust)
    st.markdown("---")

    # --- SOSTS GLOBAL UYARI (EKL-PERF-003: Lazy Alert Boot) ---
    # KALDIRILDI: Kullanıcı isteğiyle devre dışı bırakıldı (Query tasarrufu)
    pass

    # [ÖNEMLİ] Eğer QDMS seçiliyse ve top-level dispatch gerekirse buraya eklenebilir.
    # Ancak Anayasa uyarınca içerik main_app() tarafından yönetilmelidir.



def login_screen():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image(LOGO_B64, width=200)
        st.title("🔐 EKLERİSTAN QMS")

        # Veritabanından kullanıcıları direkt çek (Cache Bypass / Nuclear Option)
        with engine.connect() as conn:
            p_df = pd.read_sql(text("""
                SELECT id, ad_soyad, kullanici_adi, sifre, rol, durum, departman_id 
                FROM personel 
                WHERE durum='AKTİF' OR kullanici_adi='Admin'
            """), conn)
            # Sütun isimlerini küçük harf yap
            p_df.columns = [c.lower().strip() for c in p_df.columns]

        # Veritabanı boşsa veya hata varsa manuel Admin girişi için hazırlık
        users = p_df['kullanici_adi'].dropna().unique().tolist() if not p_df.empty else []

        # Admin her zaman listede olsun (Erişim Garantisi)
        if "Admin" not in users:
            users.append("Admin")

        user = st.selectbox("Kullanıcı Seçiniz", users)
        pwd = st.text_input("Şifre", type="password")
        remember_me = st.checkbox("Beni Hatırla (7 Gün)", value=True)

        if st.button("Giriş Yap", use_container_width=True):
            # Veritabanı Kontrolü
            if not p_df.empty:
                # Kullanıcıyı filtrele
                u_data = p_df[p_df['kullanici_adi'].astype(str) == str(user)]

                if not u_data.empty:
                    # Şifreyi direkt bu DataFrame'den al
                    db_pass = str(u_data.iloc[0]['sifre']).strip()
                    if db_pass.endswith('.0'): db_pass = db_pass[:-2]
                    
                    input_pass = str(pwd).strip()

                    # --- ANAYASA v3.2: DUAL-VALIDATION & BCRYPT LOGIN ---
                    if sifre_dogrula(input_pass, db_pass, user):
                        # [GÜNCELLEME] 1. Aktiflik Kontrolü
                        kullanici_durumu = u_data.iloc[0].get('durum')
                        if str(kullanici_durumu).strip().upper() not in ['AKTİF', 'TRUE']:
                            st.error(f"⛔ Hesabınız PASİF durumdadır ({kullanici_durumu}). Sistem yöneticiniz ile görüşün.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            # Kullanıcının rol ve bölüm bilgisini kaydet (RBAC için)
                            st.session_state.user_rol = u_data.iloc[0].get('rol', 'Personel')
                            st.session_state.user_fullname = str(u_data.iloc[0].get('ad_soyad', user)).strip().upper()
                            
                            # --- DIAGNOSTIC LOG (Gülay Gem Problemi İçin) ---
                            try:
                                from streamlit.web.server.websocket_headers import _get_websocket_headers
                                headers = _get_websocket_headers()
                                ua = headers.get("User-Agent", "Bilinmiyor")
                                audit_log_kaydet("OTURUM_BASLATILDI", f"Cihaz: {ua[:200]}", user)
                            except: pass
                            # GÜNCELLEME: Artık join ile gelen 'bolum' sütununu kullanıyoruz
                            raw_bolum = u_data.iloc[0].get('bolum', '')
                            if isinstance(raw_bolum, (pd.Series, pd.DataFrame, list)):
                                try:
                                    st.session_state.user_bolum = str(raw_bolum.iloc[0]) if hasattr(raw_bolum, 'iloc') else str(raw_bolum[0])
                                except:
                                    st.session_state.user_bolum = ""
                            else:
                                st.session_state.user_bolum = str(raw_bolum) if raw_bolum else ""

                            # Fallback: Eğer join çalışmadıysa veya boşsa, eski usül departman_id'den bulmaya çalışalım
                            if not st.session_state.user_bolum and 'departman_id' in u_data.columns:
                                try:
                                    d_id = u_data.iloc[0].get('departman_id')
                                    if d_id:
                                        d_name = run_query(f"SELECT bolum_adi FROM ayarlar_bolumler WHERE id={d_id}").iloc[0,0]
                                        st.session_state.user_bolum = d_name
                                except: pass
                            st.success(f"Hoş geldiniz, {user}!")
                            
                            # --- 13. ADAM: KALICI OTURUM OLUŞTURMA ---
                            if remember_me:
                                from logic.auth_logic import kalici_oturum_olustur
                                from streamlit.web.server.websocket_headers import _get_websocket_headers
                                headers = _get_websocket_headers()
                                ua = headers.get("User-Agent", "Bilinmiyor")
                                
                                # Veritabanından ID'yi al
                                user_id = int(u_data.iloc[0]['id'])
                                new_token = kalici_oturum_olustur(engine, user_id, cihaz_bilgisi=ua)
                                
                                # Çerezi set et (7 gün)
                                cookie_manager_obj.set("qms_remember_me", new_token, expires_at=datetime.now() + timedelta(days=7))
                            st.components.v1.html(f"""
                            <script>
                                sessionStorage.setItem('ekleristan_user', '{user}');
                                sessionStorage.setItem('ekleristan_rol', '{st.session_state.get('user_rol', 'Personel')}');
                            </script>
                            """, height=0)
                            time.sleep(0.3)
                            st.rerun()
                    else:
                        st.error("❌ Hatalı Şifre!")
                else:
                    st.error("❓ Kullanıcı kaydı bulunamadı.")
                    audit_log_kaydet("GIRIS_HATASI", f"Tanımsız kullanıcı denemesi: {user}", user)
            else:
                st.error("⚠️ Sistem şu an sadece Admin girişi kabul ediyor.")

# --- RBAC: YETKİ KONTROL FONKSİYONLARI ---
# Artık logic.auth_logic modülünden geliyor.

# --- 4. ANA UYGULAMA (MAIN APP) ---
def main_app():
    # ANAYASA v3.0: Lazy-loading db_writer (EKL-PERF-005)
    from logic.db_writer import guvenli_kayit_ekle, guvenli_coklu_kayit_ekle

    with st.sidebar:
        st.image(LOGO_B64)
        st.write(f"👤 **{st.session_state.user}**")
        
        if st.button("🚪 Sistemi Kapat (Logout)", use_container_width=True):
            from logic.auth_logic import kalici_oturum_sil
            # Çerezi ve DB izini temizle
            rt = cookie_manager_obj.get("qms_remember_me")
            if rt:
                kalici_oturum_sil(engine, rt)
                cookie_manager_obj.delete("qms_remember_me")
            
            st.session_state.logged_in = False
            st.session_state.user = ""
            st.rerun()

        st.markdown("---")

        # 13. ADAM PROTOKOLÜ: Navigasyon Senkronizasyonu (Yetki Filtreli) - Slug Bazlı
        RAW_MODULE_PAIRS = sistem_modullerini_getir()
        modul_listesi = [m[0] for m in RAW_MODULE_PAIRS if modul_gorebilir_mi(m[1])]
        if "👤 Profilim" not in modul_listesi:
            modul_listesi.append("👤 Profilim")

        if 'active_module_name' not in st.session_state or st.session_state.active_module_name not in modul_listesi:
            st.session_state.active_module_name = modul_listesi[0]

        current_active = st.session_state.active_module_name
        try:
            nav_index = modul_listesi.index(current_active)
        except:
            nav_index = 0

        menu = st.radio("MODÜLLER", modul_listesi, index=nav_index)

        if menu != current_active:
            st.session_state.active_module_name = menu
            # v3.2.7: Sidebar ve Top-Menu senkronizasyonu
            st.session_state.active_module_key = LABEL_TO_KEY.get(menu)
            st.rerun()

    # --- MODÜL YERLEŞTİRME (DISPATCHER) ---
    m_key = st.session_state.get('active_module_key')

    if m_key == "uretim_girisi":
        if not zone_girebilir_mi('ops'):
            st.error("🚫 Bu bölgeye erişim yetkiniz yok.")
            st.stop()
        from ui.uretim_ui import render_uretim_module
        render_uretim_module(engine, guvenli_kayit_ekle)

    elif m_key == "qdms":
        if not zone_girebilir_mi('mgt'):
            st.error("🚫 Bu bölgeye erişim yetkiniz yok.")
            st.stop()
        from ui.qdms_ui import qdms_main_page
        qdms_main_page(engine)

    elif m_key == "kpi_kontrol":
        if not zone_girebilir_mi('mgt'):
            st.error("🚫 Bu bölgeye erişim yetkiniz yok.")
            st.stop()
        from ui.kpi_ui import render_kpi_module
        render_kpi_module(engine, guvenli_kayit_ekle)

    elif m_key == "gmp_denetimi":
        if not zone_girebilir_mi('mgt'):
            st.error("🚫 Bu bölgeye erişim yetkiniz yok.")
            st.stop()
        from ui.gmp_ui import render_gmp_module
        render_gmp_module(engine)

    elif m_key == "personel_hijyen":
        from ui.hijyen_ui import render_hijyen_module
        render_hijyen_module(engine, guvenli_coklu_kayit_ekle)

    elif m_key == "temizlik_kontrol":
        from ui.temizlik_ui import render_temizlik_module
        render_temizlik_module(engine)

    elif m_key == "kurumsal_raporlama":
        if not zone_girebilir_mi('mgt'):
            st.error("🚫 Bu bölgeye erişim yetkiniz yok.")
            st.stop()
        from ui.raporlama_ui import render_raporlama_module
        render_raporlama_module(engine)

    elif m_key == "soguk_oda":
        # Yetki kontrolü (Dinamik yetki zaten navigasyonda yapıldı)
        from ui.soguk_oda_ui import render_sosts_module
        render_sosts_module(engine)

    elif m_key == "map_uretim":
        from ui.map_uretim.map_uretim import render_map_module
        render_map_module(engine)

    elif m_key == "performans_polivalans":
        if not zone_girebilir_mi('mgt'):
            st.error("🚫 Bu bölgeye erişim yetkiniz yok.")
            st.stop()
        from ui.performans.performans_sayfasi import performans_sayfasi_goster
        performans_sayfasi_goster()

    elif m_key == "ayarlar":
        if not zone_girebilir_mi('sys'):
            st.error("🚫 Bu bölgeye erişim yetkiniz yok.")
            st.stop()
        # Navigasyon seviyesinde yapılmış olsa da kritik blok
        from ui.ayarlar.ayarlar_orchestrator import render_ayarlar_orchestrator
        render_ayarlar_orchestrator(engine)

    elif m_key == "profilim":
        from ui.profil_ui import render_profil_modulu
        render_profil_modulu(engine)



# --- UYGULAMAYI BAŞLAT ---
if __name__ == "__main__":
    if st.session_state.get('logged_in'):
        main_app()
    else:
        # Pre-flight cookie kontrolü zaten yukarıda yapıldı, gerekiyorsa login göster
        login_screen()

# 13. ADAM: Reset butonu güncellendi (Sistemi Temizle)
if st.sidebar.button("🧹 Sistemi Temizle (Reset)", use_container_width=True):
    clear_all_cache()
    auth_keys = ['logged_in', 'user', 'user_rol', 'user_bolum', 'yetki_haritasi']
    for key in list(st.session_state.keys()):
        if key not in auth_keys:
            del st.session_state[key]
    st.toast("🧹 Önbellek temizlendi, yetkiler yenilendi.")
    st.rerun()
