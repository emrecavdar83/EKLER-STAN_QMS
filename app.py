# Ekleristan QMS - V: 2026-03-04-1000-SOZamanRapor-Fix
import streamlit as st
import pandas as pd
import graphviz
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import pytz
import os


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

# Logic modülünden fonksiyonları import et
from logic.settings_logic import (
    suggest_username,
    assign_role_by_hierarchy,
    clean_department_ids,
    validate_personnel_data,
    flatten_department_hierarchy,
    find_excel_column,
    parse_location_ids,
    format_location_ids,
    execute_with_transaction
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
    kullanici_yetkisi_var_mi
)

from logic.sync_handler import render_sync_button

from logic.cache_manager import (
    clear_personnel_cache,
    clear_department_cache,
    clear_all_cache
)

# UI MODULLERI (MODULAR UI)
from ui.soguk_oda_ui import render_sosts_module
from ui.uretim_ui import render_uretim_module
from ui.kpi_ui import render_kpi_module
from ui.gmp_ui import render_gmp_module
from ui.hijyen_ui import render_hijyen_module
from ui.temizlik_ui import render_temizlik_module
from ui.raporlama_ui import render_raporlama_module
from ui.ayarlar.ayarlar_orchestrator import render_ayarlar_orchestrator
from ui.profil_ui import render_profil_modulu
from logic.db_writer import guvenli_kayit_ekle, guvenli_coklu_kayit_ekle
import soguk_oda_utils


# --- 1. AYARLAR & VERİTABANI BAĞLANTISI ---
from database.connection import get_engine, auto_fix_data, guvenli_admin_olustur

# Veritabanı motorunu al
engine = get_engine()

# Başlangıçta 1 kez çalıştır (Oturum başına)
if 'global_data_fixed' not in st.session_state:
    auto_fix_data()
    st.session_state.global_data_fixed = True


# --- MOBİL UYUMLULUK İÇİN RESPONSIVE CSS ---
st.markdown("""
<style>
    /* Mobil cihazlar için responsive düzenlemeler */
    @media (max-width: 768px) {
        /* Sidebar'ı mobilde daralt */
        .css-1d391kg { padding: 1rem 0.5rem; }

        /* Tabloları yatay kaydırılabilir yap */
        .stDataFrame, .dataframe {
            overflow-x: auto;
            display: block;
            max-width: 100%;
        }

        /* Metric kartlarını tek sütuna düşür */
        [data-testid="stMetricValue"] { font-size: 1.2rem !important; }

        /* Butonları tam genişlik yap */
        .stButton > button { width: 100% !important; }

        /* Graphviz şemalarını scroll ile göster */
        .stGraphVizChart { overflow: auto; max-width: 100vw; }
    }

    /* Tablet için orta düzey ayarlar */
    @media (min-width: 769px) and (max-width: 1024px) {
        .stDataFrame { max-width: 100%; overflow-x: auto; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. VERİ İŞLEMLERİ ---


ADMIN_USERS, CONTROLLER_ROLES = get_user_roles()

# CACHING: Veri çekme işlemini önbelleğe al (TTL: 60 saniye)
# Böylece her tıklamada tekrar tekrar SQL sorgusu atmaz


# --- YENİ VARDİYA SİSTEMİ YARDIMCI FONKSİYONLARI ---

# --- VERİTABANI BAŞLANGIÇ KONTROLÜ (CLOUD İÇİN KRİTİK) ---
# Bağlantıyı test et ve hemen kapat (connection leak önleme)
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1 FROM personel LIMIT 1"))
except Exception as e:
    # Hata yönetimi
    pass

LOGO_URL = "https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png"

# Admin listesi get_user_roles() ile cache'den geliyor.
# Geçmişteki try-except bloğu yerine artık merkezi cache devrede.

# Zaman Fonksiyonu
def get_istanbul_time():
    # Atomik Zaman: Milisaniyeleri temizle (.replace(microsecond=0))
    now = datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)

# --- 3. ARAYÜZ BAŞLANGICI ---





# --- 3. ARAYÜZ BAŞLANGICI ---
st.set_page_config(page_title="Ekleristan QMS", layout="wide", page_icon="🏭")
st.sidebar.title("Ekleristan QMS")
st.sidebar.caption("v2.0.0 - Sistematik Yönetim 🛡️")
st.sidebar.success("✅ 13. ADAM SİSTEMİ ONAYLANDI")
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
st.success("✅ SİSTEM ANALİZİ TAMAMLANDI - v2.0.0 AKTİF")

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
        # QR linki yeni oturum açar; giriş yoksa 'Saha_Mobil' olarak kabul et
        if not st.session_state.get('logged_in'):
            st.session_state.logged_in = True
            st.session_state.user = "Saha_Mobil"
            st.session_state.user_rol = "Personel"
            st.session_state.user_bolum = ""

# --- 13. ADAM: HİBRİT NAVİGASYON HUB (ÖLÜMSÜZ MENÜ) ---
# Hamburger menü krizini kökten çözer.
if st.session_state.logged_in:
    # Sayfanın en tepesine, sidebar'dan bağımsız menü koyuyoruz.

    # Modül Listesi (Dinamik - Anayasa v2.0)
    NAV_MODULES = sistem_modullerini_getir()
    if "👤 Profilim" not in NAV_MODULES:
        NAV_MODULES.append("👤 Profilim")

    # State tabanlı navigasyon
    if 'active_module_name' not in st.session_state:
        st.session_state.active_module_name = NAV_MODULES[0]

    # QR yönlendirme mantığı pages/ yapısına bırakıldı

    # Üst Menü (Mobilde Hayat Kurtarır)
    secim_ust = st.selectbox(
        "📍 HIZLI MENÜ (MODÜL SEÇİNİZ):",
        NAV_MODULES,
        index=NAV_MODULES.index(st.session_state.active_module_name) if st.session_state.active_module_name in NAV_MODULES else 0
    )

    # Seçimi kaydet
    st.session_state.active_module_name = secim_ust
    st.markdown("---")

    # --- SOSTS GLOBAL UYARI (Geciken Ölçümler) ---
    try:
        if hasattr(soguk_oda_utils, 'get_overdue_summary'):
            # PERFORMANS: Her saniye değil, 5 dakikada bir kontrol et
            last_alert_check = st.session_state.get("sosts_last_alert_check", 0)
            current_time = time.time()
            
            if (current_time - last_alert_check) > 300: # 5 Dakika
                df_gecikme = soguk_oda_utils.get_overdue_summary(engine)
                st.session_state.sosts_gecikme_cache = df_gecikme
                st.session_state.sosts_last_alert_check = current_time
            
            df_gecikme = st.session_state.get("sosts_gecikme_cache", pd.DataFrame())
            
            if not df_gecikme.empty:
                total_gecikme = df_gecikme['gecikme_sayisi'].sum()
                oda_list = ", ".join(df_gecikme['oda_adi'].tolist())
                st.error(f"🚨 **DİKKAT:** {total_gecikme} adet gecikmiş soğuk oda ölçümü var! (Odalar: {oda_list})", icon="🚨")
    except Exception:
        pass



def login_screen():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image(LOGO_URL, width=200)
        st.title("🔐 EKLERİSTAN QMS")

        # Veritabanından kullanıcıları çek
        p_df = veri_getir("Ayarlar_Personel")

        # Veritabanı boşsa veya hata varsa manuel Admin girişi için hazırlık
        users = []
        if not p_df.empty:
            # Sütun isimlerini küçük harf yap ve boşlukları temizle
            p_df.columns = [c.lower().strip() for c in p_df.columns]
            if 'kullanici_adi' in p_df.columns:
                users = p_df['kullanici_adi'].dropna().unique().tolist()

        # Admin her zaman listede olsun (Erişim Garantisi)
        if "Admin" not in users:
            users.append("Admin")

        user = st.selectbox("Kullanıcı Seçiniz", users)
        pwd = st.text_input("Şifre", type="password")

        if st.button("Giriş Yap", use_container_width=True):
            # Veritabanı Kontrolü (Admin dahil her şey DB'den)
            if not p_df.empty:
                # Kullanıcıyı filtrele
                u_data = p_df[p_df['kullanici_adi'].astype(str) == str(user)]

                if not u_data.empty:
                    # Şifreleri string (metin) tipine çevirip karşılaştır (örnek: 1234.0 -> 1234)
                    db_pass = str(u_data.iloc[0]['sifre']).strip()
                    if db_pass.endswith('.0'): db_pass = db_pass[:-2]

                    input_pass = str(pwd).strip()

                    if input_pass == db_pass:
                        # [GÜNCELLEME] 1. Aktiflik Kontrolü
                        kullanici_durumu = u_data.iloc[0].get('durum')
                        if str(kullanici_durumu).strip().upper() not in ['AKTİF', 'TRUE']:
                            st.error(f"⛔ Hesabınız PASİF durumdadır ({kullanici_durumu}). Sistem yöneticiniz ile görüşün.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            # Kullanıcının rol ve bölüm bilgisini kaydet (RBAC için)
                            st.session_state.user_rol = u_data.iloc[0].get('rol', 'Personel')
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
                            st.components.v1.html(f"""
                            <script>
                                sessionStorage.setItem('ekleristan_user', '{user}');
                                sessionStorage.setItem('ekleristan_rol', '{st.session_state.get('user_rol', 'Personel')}');
                            </script>
                            """, height=0)
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.error("❌ Hatalı Şifre!")
                else:
                    st.error("❓ Kullanıcı kaydı bulunamadı.")
            else:
                st.error("⚠️ Sistem şu an sadece Admin girişi kabul ediyor.")

# --- RBAC: YETKİ KONTROL FONKSİYONLARI ---
# Artık logic.auth_logic modülünden geliyor.

# --- 4. ANA UYGULAMA (MAIN APP) ---
def main_app():
    with st.sidebar:
        st.image(LOGO_URL)
        st.write(f"👤 **{st.session_state.user}**")

        # DEBUG: Sevcan Hanım için rol kontrolü (Geçici)
        if str(st.session_state.user) == 'sevcanalbas':
            st.code(f"Rol: {st.session_state.get('user_rol')}\nBölüm: {st.session_state.get('user_bolum')}")

        st.markdown("---")

        # 13. ADAM PROTOKOLÜ: Navigasyon Senkronizasyonu
        # Hem üstteki Selectbox hem de Sidebar Radio aynı state'i yönetmeli.

        modul_listesi = sistem_modullerini_getir()
        if "👤 Profilim" not in modul_listesi:
            modul_listesi.append("👤 Profilim")

        # 1. Mevcut aktif modülü bul (Varsayılan: Üretim)
        if 'active_module_name' not in st.session_state:
            st.session_state.active_module_name = modul_listesi[0]

        current_active = st.session_state.active_module_name

        # 2. Indexi belirle
        try:
            nav_index = modul_listesi.index(current_active)
        except:
            nav_index = 0

        # 3. Radio butonunu çiz (Index ile durumu yönet)
        menu = st.radio("MODÜLLER", modul_listesi, index=nav_index)

        # 4. Çift Yönlü Senkronizasyon (Sidebar değişirse Header'ı güncelle)
        if menu != current_active:
            st.session_state.active_module_name = menu
            st.rerun()

        st.markdown("---")

        # SİSTEM DURUMU (LOKAL GÖSTERGESİ)
        if 'sqlite' in str(engine.url):
             st.info("🟢 MOD: LOKAL (SQLite)")
        else:
             st.warning("☁️ MOD: CANLI (Bulut)")

        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.rerun()

        if st.button("🧹 Sistemi Temizle (Reset)"):
            clear_all_cache()
            # KRİTİK: Oturum (Auth) bilgilerini KORU, diğer her şeyi sil
            auth_keys = ['logged_in', 'user', 'user_rol', 'user_bolum', 'global_data_fixed']
            for key in list(st.session_state.keys()):
                if key not in auth_keys:
                    del st.session_state[key]
            
            st.toast("🧹 Önbellek ve filtreler temizlendi, oturumunuz korundu.")
            time.sleep(1)
            st.rerun()

    # >>> MODÜL 1: ÜRETİM KAYIT SİSTEMİ <<<
    if menu == "🏭 Üretim Girişi":
        render_uretim_module(engine, guvenli_kayit_ekle)

    # >>> MODÜL 2: KPI & KALİTE KONTROL <<<
    elif menu == "🍩 KPI & Kalite Kontrol":
        render_kpi_module(engine, guvenli_kayit_ekle)


    # >>> MODÜL: GMP DENETİMİ <<<
    elif menu == "🛡️ GMP Denetimi":
        render_gmp_module(engine)

    # >>> MODÜL 3: PERSONEL HİJYEN <<<
    elif menu == "🧼 Personel Hijyen":
        render_hijyen_module(engine, guvenli_coklu_kayit_ekle)
    # >>> MODÜL: TEMİZLİK VE SANİTASYON <<<
    elif menu == "🧹 Temizlik Kontrol":
        render_temizlik_module(engine)

    # >>> MODÜL: KURUMSAL RAPORLAMA <<<
    elif menu == "📊 Kurumsal Raporlama":
        render_raporlama_module(engine)
    # >>> MODÜL: SOĞUK ODA SICAKLIKLARI (SOSTS) <<<
    elif menu == "❄️ Soğuk Oda Sıcaklıkları":
        # Yetki kontrolü (Anayasa Madde 5)
        if not kullanici_yetkisi_var_mi(menu, "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.stop()

        # Modüler UI Çağrısı (Yeni Entegre Yapı)
        render_sosts_module(engine)


    # >>> MODÜL: AYARLAR <<<
    elif menu == "⚙️ Ayarlar":
        # Yetki kontrolü - Ayarlar sadece Admin'e açık
        if not kullanici_yetkisi_var_mi(menu, "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.info("💡 Ayarlar modülüne erişim için Admin yetkisi gereklidir.")
            st.stop()
        
        # Modüler Ayarlar Orkestratörü
        render_ayarlar_orchestrator(engine)

    # >>> MODÜL: PROFİLİM <<<
    elif menu == "👤 Profilim":
        render_profil_modulu(engine)



# --- UYGULAMAYI BAŞLAT ---
if __name__ == "__main__":
    if st.session_state.logged_in:
        main_app()
    else:
        login_screen()
