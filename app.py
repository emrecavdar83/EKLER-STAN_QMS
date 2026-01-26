import streamlit as st
import pandas as pd
import graphviz
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import pytz

from constants import (
    POSITION_LEVELS,
    MANAGEMENT_LEVELS,
    STAFF_LEVELS,
    get_position_name,
    get_position_icon,
    get_position_color,
    get_position_label
)

# --- 1. AYARLAR & VERİTABANI BAĞLANTISI ---
import os

# --- 1. AYARLAR & VERİTABANI BAĞLANTISI ---
import os

# CACHING: Veritabanı bağlantısını önbelleğe al (Her seferinde bağlanmasın)
@st.cache_resource
def init_connection():
    # Önce Streamlit Cloud Secret kontrolü, yoksa Yerel SQLite
    # POOLING: Bağlantıları havuzda tut ve canlılığını kontrol et (Supabase için kritik)
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
        return create_engine(
            db_url, 
            pool_size=10, 
            max_overflow=20, 
            pool_pre_ping=True, # Bağlantı kopmalarını otomatik algıla
            pool_recycle=300    # 5 dakikada bir bağlantıları yenile
        )
    else:
        db_url = 'sqlite:///ekleristan_local.db'
        return create_engine(db_url, connect_args={'check_same_thread': False})

engine = init_connection()

def guvenli_admin_olustur():
    """Admin kullanıcısı yoksa oluşturur (Canlı ve Yerel ortamda ortak)"""
    try:
        with engine.connect() as conn:
            # Personel tablosunda Admin kullanıcı adı var mı kontrol et
            res = conn.execute(text("SELECT COUNT(*) FROM personel WHERE kullanici_adi = 'Admin'")).fetchone()
            if res[0] == 0:
                # Varsayılan Admini Ekle
                conn.execute(text("""
                    INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye)
                    VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'Admin', 'AKTİF', 0)
                """))
                conn.commit()
                return True
    except Exception:
        pass
    return False

# İlk açılışta kontrol et
guvenli_admin_olustur()

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


# --- MERKEZİ CACHING SİSTEMİ (LİGHTNİNG SPEED) ---
@st.cache_data(ttl=600) # 10 dakika boyunca aynı sorguyu DB'ye atmaz
def run_query(query, params=None):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)

@st.cache_data(ttl=3600) # Rol bazlı listeler 1 saat cache'de kalsın
def get_user_roles():
    try:
        with engine.connect() as conn:
            admins = [r[0] for r in conn.execute(text("SELECT ad_soyad FROM personel WHERE rol IN ('Admin', 'Yönetim') AND ad_soyad IS NOT NULL")).fetchall()]
            controllers = [r[0] for r in conn.execute(text("SELECT ad_soyad FROM personel WHERE rol IN ('Admin', 'Kalite Sorumlusu', 'Vardiya Amiri') AND ad_soyad IS NOT NULL")).fetchall()]
            return admins, controllers

    except Exception as e:
        return [], []

@st.cache_data(ttl=600)
def get_department_hierarchy():
    """Veritabanından departmanları çekip sadece isim listesi döndürür (Max 3 kademe)"""
    try:
        df_dept = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif IS TRUE ORDER BY sira_no")
        if df_dept.empty:
            return []
        
        hierarchy_list = []
        MAX_LEVEL = 3  # Maksimum derinlik
        
        # Recursive Fonksiyon (Internal)
        def build_hierarchy(parent_id, level):
            # Seviye kontrolü
            if level > MAX_LEVEL:
                return
                
            # Bu parent'a bağlı olanları bul
            if parent_id is None:
                current = df_dept[df_dept['ana_departman_id'].isnull() | (df_dept['ana_departman_id'] == 0) | (df_dept['ana_departman_id'].isna())]
            else:
                current = df_dept[df_dept['ana_departman_id'] == parent_id]
                
            for _, row in current.iterrows():
                d_id = row['id']
                name = row['bolum_adi']
                
                # Sadece departman adını ekle (tam yol değil)
                hierarchy_list.append(name)
                
                # Alt departmanları da ara (seviye + 1)
                build_hierarchy(d_id, level + 1)
                
        build_hierarchy(None, 1)
        return hierarchy_list
    except Exception as e:
        return []


def render_sync_button():
    """Ayarlar modülü için gerçek Lokal -> Cloud senkronizasyon butonu"""
    st.markdown("---")
    col_sync1, col_sync2 = st.columns([3, 1])
    with col_sync1:
        st.info("💡 **Cloud Sync:** Lokalde yaptığınız tüm yapılandırmaları (Lokasyon, Personel, Plan, GMP vb.) canlı sisteme aktarır.")
        
    with col_sync2:
        if st.button("🚀 Ayarları Canlıya Gönder", key=f"btn_sync_{int(time.time()*1000)}", type="primary", use_container_width=True):
            # 1. Ortam Kontrolü
            is_local = 'sqlite' in str(engine.url)
            
            if not is_local:
                st.warning("⚠️ Zaten Bulut/Canlı veritabanına bağlısınız. Bu işlem sadece Lokalde çalışır.")
                return

            # 2. Canlı Bağlantı Bilgisi (Secret) Kontrolü
            cloud_url = None
            try:
                cloud_url = st.secrets.get("DB_URL")
            except: pass
            
            if not cloud_url:
                st.error("❌ '.streamlit/secrets.toml' dosyasında 'DB_URL' bulunamadı.")
                st.caption("Lütfen canlı veritabanı bağlantı adresini yapılandırın.")
                return

            # 3. Senkronizasyon Başlat
            with st.status("🚀 Cloud Sync Başlatılıyor...", expanded=True) as status:
                try:
                    # Canlıya bağlan
                    status.write("☁️ Canlı veritabanına bağlanılıyor...")
                    try:
                        # psycopg2 gerekebilir, veya mevcut driver
                        cloud_engine = create_engine(cloud_url)
                        # Bağlantı testi
                        with cloud_engine.connect() as test_conn:
                            test_conn.execute(text("SELECT 1"))
                    except Exception as e:
                        status.update(label="❌ Bağlantı Hatası!", state="error")
                        st.error(f"Canlı veritabanına bağlanılamadı: {e}")
                        return

                    # Tablo Listesi (Sıra Önemli: Parent -> Child)
                    tables_to_sync = [
                        "ayarlar_bolumler",      # Departmanlar
                        "ayarlar_yetkiler",      # Roller/Yetkiler
                        "personel",              # Kullanıcılar
                        "lokasyonlar",           # Fiziksel Yerleşim
                        "proses_tipleri",        # Proses Tanımları
                        "lokasyon_proses_atama", # Proses Atamaları
                        "tanim_metotlar",        # Temizlik Yöntemleri
                        "kimyasal_envanter",     # Kimyasallar
                        "ayarlar_temizlik_plani",# Master Plan
                        "gmp_soru_havuzu"        # GMP Soruları
                    ]
                    
                    for tbl in tables_to_sync:
                        status.write(f"📦 {tbl} tablosu aktarılıyor...")
                        try:
                            # Lokaldan Oku
                            df_local = pd.read_sql(f"SELECT * FROM {tbl}", engine)
                            
                            if not df_local.empty:
                                # Canlıya Yaz (Replace: Tam eşitleme)
                                # Not: Cascade hatalarını önlemek için önce canlıdaki tabloyu truncate etmek daha temiz olabilir
                                # ama 'replace' metodu tabloyu drop-create yapar, bu da view'ları bozabilir!
                                # En güvenlisi: 'append' ama öncesinde 'delete'.
                                
                                # Pandas to_sql 'replace' kullanırsak Viewler bozulabilir.
                                # O yüzden 'if_exists=append' ve öncesinde 'delete' yapacağız.
                                
                                with cloud_engine.begin() as cloud_conn:
                                    # Önce temizle
                                    cloud_conn.execute(text(f"DELETE FROM {tbl}")) 
                                    # Şimdi ekle
                                    df_local.to_sql(tbl, cloud_conn, if_exists='append', index=False)
                            
                        except Exception as e_tbl:
                            st.warning(f"⚠️ {tbl} aktarılırken uyarı: {e_tbl}")
                            continue # Diğer tabloya geç
                            
                    status.update(label="✅ Senkronizasyon Tamamlandı!", state="complete", expanded=False)
                    st.success("Tüm ayarlar başarıyla canlı sisteme gönderildi! 🎉")
                    st.toast("Veri transferi başarılı!", icon="✅")
                    
                except Exception as e:
                    status.update(label="❌ Genel Hata", state="error")
                    st.error(f"Beklenmeyen hata: {e}")

# Personel Hiyerarşisini Getir (YENİ - Organizasyon Şeması İçin)
@st.cache_data(ttl=5)  # 5 saniye - personel değişikliklerini hızlı göster
def get_personnel_hierarchy():
    """Personel tablosundan organizasyon hiyerarşisini oluşturur (v_organizasyon_semasi view'ından)"""
    try:
        df = pd.read_sql("SELECT * FROM v_organizasyon_semasi", engine)
    except:
        # View henüz oluşturulmamışsa fallback: Direkt personel tablosundan çek
        try:
            df = pd.read_sql("""
                SELECT 
                    p.id, p.ad_soyad, p.gorev, p.rol, 
                    COALESCE(d.bolum_adi, 'Tanımsız') as departman,
                    p.kullanici_adi, p.durum, p.vardiya,
                    COALESCE(p.pozisyon_seviye, 5) as pozisyon_seviye,
                    p.yonetici_id, p.departman_id
                FROM personel p
                LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
                WHERE p.ad_soyad IS NOT NULL
            """, engine)
        except Exception as e:
            # Hata durumunda boş DataFrame döndür
            return pd.DataFrame()
    
    if df.empty:
        return df

    # ═══════════════════════════════════════════════════════════
    # VERİ TEMİZLİĞİ VE VARSAYILAN DEĞERLER (SABİTLER)
    # ═══════════════════════════════════════════════════════════
    # Bu bölüm, eksik verili personellerin şemada kaybolmasını önler.
    
    # 1. Pozisyon Seviyesi: Boşsa 5 (Personel - Mavi Yaka) olarak kabul et
    if 'pozisyon_seviye' in df.columns:
        df['pozisyon_seviye'] = pd.to_numeric(df['pozisyon_seviye'], errors='coerce').fillna(5).astype(int)
    
    # 2. Departman ID: Boşsa 0 (Tanımsız)
    if 'departman_id' in df.columns:
        df['departman_id'] = pd.to_numeric(df['departman_id'], errors='coerce').fillna(0).astype(int)
        
    # 3. Sıralama: Seviye > Departman > İsim
    if 'ad_soyad' in df.columns:
        try:
            df = df.sort_values(['pozisyon_seviye', 'departman_id', 'ad_soyad'])
        except:
            pass # Sıralama hatası olursa yoksay
            
    # 4. Aktiflik Filtresi: Sadece AKTİF personeli göster
    if 'durum' in df.columns:
        # Case-insensitive filtreleme ve boşluk temizliği
        df = df[df['durum'].astype(str).str.strip().str.upper() == 'AKTİF']

    return df


ADMIN_USERS, CONTROLLER_ROLES = get_user_roles()

# CACHING: Veri çekme işlemini önbelleğe al (TTL: 60 saniye)
# Böylece her tıklamada tekrar tekrar SQL sorgusu atmaz
@st.cache_data(ttl=60)
def cached_veri_getir(tablo_adi):
    queries = {
        "Ayarlar_Personel": "SELECT * FROM personel WHERE kullanici_adi IS NOT NULL",
        "Ayarlar_Urunler": "SELECT * FROM ayarlar_urunler",
        "Depo_Giris_Kayitlari": "SELECT * FROM depo_giris_kayitlari ORDER BY id DESC LIMIT 50",
        "Ayarlar_Fabrika_Personel": "SELECT * FROM personel WHERE ad_soyad IS NOT NULL",
        "Ayarlar_Temizlik_Plani": "SELECT * FROM ayarlar_temizlik_plani",
        "Tanim_Bolumler": "SELECT * FROM tanim_bolumler ORDER BY id",
        "Tanim_Ekipmanlar": "SELECT * FROM tanim_ekipmanlar",
        "Tanim_Metotlar": "SELECT * FROM tanim_metotlar",
        "Kimyasal_Envanter": "SELECT * FROM kimyasal_envanter ORDER BY id",
        "GMP_Soru_Havuzu": "SELECT * FROM gmp_soru_havuzu",
        "Ayarlar_Bolumler": "SELECT * FROM ayarlar_bolumler WHERE aktif = TRUE ORDER BY sira_no"
    }
    
    sql = queries.get(tablo_adi)
    if not sql: return pd.DataFrame()
    
    try:
        df = run_query(sql)
        df.columns = [c.lower().strip() for c in df.columns] 
        return df
    except:
        return pd.DataFrame()

# Wrapper fonksiyon (Eski kod bozulmasın diye aynı ismi kullanıyoruz)
def veri_getir(tablo_adi):
    return cached_veri_getir(tablo_adi)

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
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

# --- 2. VERİ İŞLEMLERİ ---
# Not: veri_getir zaten yukarıda tanımlandı.

def guvenli_kayit_ekle(tablo_adi, veri):
    try:
        # DB işlemi - Context manager ile bağlantıyı otomatik kapat
        with engine.connect() as conn:
            if tablo_adi == "Depo_Giris_Kayitlari":
                sql = """INSERT INTO depo_giris_kayitlari (tarih, vardiya, kullanici, islem_tipi, urun, lot_no, miktar, fire, notlar, zaman_damgasi)
                         VALUES (:t, :v, :k, :i, :u, :l, :m, :f, :n, :z)"""
                params = {"t":veri[0], "v":veri[1], "k":veri[2], "i":veri[3], "u":veri[4], "l":veri[5], "m":veri[6], "f":veri[7], "n":veri[8], "z":veri[9]}
                conn.execute(text(sql), params)
                conn.commit()
                
                # SEÇİCİ CACHE TEMİZLEME: Sadece Depo kayıtları cache'ini temizle
                cached_veri_getir.clear()
                return True
                
            elif tablo_adi == "Urun_KPI_Kontrol":
                # ... (SQL Kodu) ...
                sql = """INSERT INTO urun_kpi_kontrol (tarih, saat, vardiya, urun, lot_no, stt, numune_no, olcum1, olcum2, olcum3, karar, kullanici, tat, goruntu, notlar)
                         VALUES (:t, :sa, :v, :u, :l, :stt, :num, :o1, :o2, :o3, :karar, :kul, :tat, :gor, :notlar)"""
                params = {
                    "t": veri[0], "sa": veri[1], "v": veri[2], "u": veri[3],
                    "l": veri[5], "stt": veri[6], "num": veri[7],
                    "o1": veri[8], "o2": veri[9], "o3": veri[10],
                    "karar": veri[11], "kul": veri[12],
                    "tat": veri[16], "gor": veri[17], "notlar": veri[18]
                }
                conn.execute(text(sql), params)
                conn.commit()
                
                # SEÇİCİ CACHE TEMİZLEME: Sadece KPI cache'ini temizle
                cached_veri_getir.clear()
                return True

    except Exception as e:
        st.error(f"SQL Hatası: {e}")
        return False
    return False

def guvenli_coklu_kayit_ekle(tablo_adi, veri_listesi):
    try:
        # Context manager ile bağlantıyı otomatik kapat
        with engine.connect() as conn:
            if tablo_adi == "Hijyen_Kontrol_Kayitlari":
                sql = """INSERT INTO hijyen_kontrol_kayitlari (tarih, saat, kullanici, vardiya, bolum, personel, durum, sebep, aksiyon)
                         VALUES (:t, :s, :k, :v, :b, :p, :d, :se, :a)"""
                for row in veri_listesi:
                     params = {"t":row[0], "s":row[1], "k":row[2], "v":row[3], "b":row[4], "p":row[5], "d":row[6], "se":row[7], "a":row[8]}
                     conn.execute(text(sql), params)
                conn.commit()
                return True
    except Exception as e:
        st.error(f"Toplu Kayıt Hatası: {e}")
        return False

# --- 3. ARAYÜZ BAŞLANGICI ---
st.set_page_config(page_title="Ekleristan QMS", layout="wide", page_icon="🏭")

st.markdown("""
<style>
/* 1. Buton ve Radyo Buton Özelleştirme */
div.stButton > button:first-child {background-color: #8B0000; color: white; width: 100%; border-radius: 5px;}
.stRadio > label {font-weight: bold;}

/* 2. Header Branding Temizliği - Toolbar'ı Gizle */
/* Bu bölüm header'ı tamamen yok eder. Sidebar butonu için yer açmamız lazım. */
[data-testid="stToolbar"], 
[data-testid="stHeader"] {
    visibility: hidden !important; 
    height: 0px !important;
    padding: 0px !important;
    margin: 0px !important;
}

/* Dekoratif header çizgisi varsa onu da gizle */
[data-testid="stDecoration"] {
    display: none !important;
}

/* GÜVENLİK: Kod erişimini sağlayan GitHub ve Deploy butonlarını TAMAMEN gizle */
.stAppDeployButton,
[data-testid="stManageAppButton"],
[data-testid="stHeaderActionElements"],
.stActionButton,
.viewerBadge_container__1QSob,
.styles_viewerBadge__1yB5_,
.viewerBadge-link {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Footer'ı gizle */
footer {
    display: none !important;
    visibility: hidden !important;
}

/* 3. Menü Butonunu (Hamburger - Sağ Üst) - GİZLE */
#MainMenu {
    visibility: hidden !important;
    display: none !important;
}

/* 4. Sol Üst Sidebar Butonunu (Hamburger/Ok) KESİNLİKLE KORU */
/* Header gizlendiği için bu buton kaybolabilir, o yüzden FIXED pozisyon veriyoruz */
button[data-testid="stSidebarCollapseButton"], 
button[aria-label="Open sidebar"], 
button[aria-label="Close sidebar"],
[data-testid="stSidebarNav"] button {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 99999999 !important; /* En üstte */
    position: fixed !important;   /* Sayfadan bağımsız */
    top: 10px !important;         /* Tepeye sabitle */
    left: 10px !important;        /* Sola sabitle */
    background-color: #8B0000 !important; 
    color: white !important;
    border-radius: 5px !important;
    width: 40px !important;
    height: 40px !important;
}

/* Mobil için Konum Sabitleme */
@media screen and (max-width: 768px) {
    button[data-testid="stSidebarCollapseButton"],
    button[aria-label="Open sidebar"] {
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        scale: 1.1;
    }
}
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = ""

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
                        # [GÜNCELLEME] 1. Aktiflik Kontrolü
                        kullanici_durumu = u_data.iloc[0].get('durum')
                        # Eğer durum boşsa varsayılan olarak AKTİF kabul ETMEYELİM, ya da veritabanında düzelttik.
                        # Ama güvenli olması için: Sadece net 'AKTİF' yazanlar girebilsin.
                        if kullanici_durumu != 'AKTİF':
                            st.error(f"⛔ Hesabınız PASİF durumdadır ({kullanici_durumu}). Sistem yöneticiniz ile görüşün.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            # Kullanıcının rol ve bölüm bilgisini kaydet (RBAC için)
                            st.session_state.user_rol = u_data.iloc[0].get('rol', 'Personel')
                            st.session_state.user_bolum = u_data.iloc[0].get('bolum', '')
                            st.success(f"Hoş geldiniz, {user}!")
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.error("❌ Hatalı Şifre!")
                else:
                    st.error("❓ Kullanıcı kaydı bulunamadı.")
            else:
                st.error("⚠️ Sistem şu an sadece Admin girişi kabul ediyor.")

# --- RBAC: YETKİ KONTROL FONKSİYONLARI ---
# Modül isimleri eşlemesi (Menu -> Veritabanı)
MODUL_ESLEME = {
    "🏭 Üretim Girişi": "Üretim Girişi",
    "🍩 KPI & Kalite Kontrol": "KPI Kontrol",
    "🛡️ GMP Denetimi": "GMP Denetimi",
    "🧼 Personel Hijyen": "Personel Hijyen",
    "🧹 Temizlik Kontrol": "Temizlik Kontrol",
    "📊 Kurumsal Raporlama": "Raporlama",
    "⚙️ Ayarlar": "Ayarlar"
}

@st.cache_data(ttl=300)  # 5 dakika cache
def kullanici_yetkisi_getir(rol_adi, modul_adi):
    """Belirli rol için modül yetkisini veritabanından çeker"""
    try:
        with engine.connect() as conn:
            sql = text("""
                SELECT erisim_turu FROM ayarlar_yetkiler 
                WHERE rol_adi = :rol AND modul_adi = :modul
            """)
            result = conn.execute(sql, {"rol": rol_adi, "modul": modul_adi}).fetchone()
            return result[0] if result else "Yok"
    except:
        return "Yok"

def kullanici_yetkisi_var_mi(menu_adi, gereken_yetki="Görüntüle"):
    """Kullanıcının belirli modüle erişim yetkisini kontrol eder"""
    user_rol = st.session_state.get('user_rol', 'Personel')
    
    # Admin her şeye erişebilir
    if user_rol == 'Admin':
        return True
    
    # Modül adını veritabanı formatına çevir
    modul_adi = MODUL_ESLEME.get(menu_adi, menu_adi)
    
    # Yetkiyi kontrol et
    erisim = kullanici_yetkisi_getir(user_rol, modul_adi)
    
    if gereken_yetki == "Görüntüle":
        return erisim in ["Görüntüle", "Düzenle"]
    elif gereken_yetki == "Düzenle":
        return erisim == "Düzenle"
    return False

def bolum_bazli_urun_filtrele(urun_df):
    """Bölüm Sorumlusu için ürün listesini hiyerarşik olarak filtreler"""
    user_rol = st.session_state.get('user_rol', 'Personel')
    user_bolum = st.session_state.get('user_bolum', '')
    
    # 1. Admin ve Üst Yönetim her şeyi görsün
    if user_rol in ['Admin', 'Yönetim', 'Kalite Sorumlusu']:
        return urun_df
    
    # 2. Vardiya Amiri Filtresi (Sadece kendi bölümü varsa filtrele, yoksa genel görür)
    if user_rol == 'Vardiya Amiri' and not user_bolum:
        return urun_df
    
    # 2. Bölüm Sorumlusu Filtresi
    # Eğer ürünlerde 'sorumlu_departman' kolonu varsa (Yeni Sistem)
    if 'sorumlu_departman' in urun_df.columns and user_bolum:
        try:
            # Mantık: 
            # A) Ürünün departmanı BOŞ ise -> Herkes görür (Henüz atanmamış/Genel ürün)
            # B) Ürünün departman adı, kullanıcının bölüm adını İÇERİYORSA -> Görür (Hiyerarşik Eşleşme)
            #    Örn: Ürün Yeri='Üretim > Pataşu', Kullanıcı='Pataşu' -> Eşleşir.
            #    Örn: Ürün Yeri='Üretim > Pataşu', Kullanıcı='Üretim' -> Eşleşir.
            
            # fillna('') ile NaN değerleri boş string yapıyoruz ki hata vermesin
            mask_bos = urun_df['sorumlu_departman'].isna() | (urun_df['sorumlu_departman'] == '')
            mask_eslesme = urun_df['sorumlu_departman'].astype(str).str.contains(str(user_bolum), case=False, na=False)
            
            filtreli = urun_df[mask_bos | mask_eslesme]
            return filtreli
            
        except Exception as e:
            st.warning(f"Filtreleme hatası: {e}")
            return urun_df

    # 3. Eski Sistem ('uretim_bolumu' varsa) - Geriye dönük uyumluluk
    elif 'uretim_bolumu' in urun_df.columns and user_bolum:
        return urun_df[urun_df['uretim_bolumu'].astype(str).str.upper() == str(user_bolum).upper()]
    
    return urun_df

# --- 4. ANA UYGULAMA (MAIN APP) ---
def main_app():
    with st.sidebar:
        st.image(LOGO_URL)
        st.write(f"👤 **{st.session_state.user}**")
        st.markdown("---")
        menu = st.radio("MODÜLLER", [
            "🏭 Üretim Girişi", 
            "🍩 KPI & Kalite Kontrol", 
            "🛡️ GMP Denetimi",
            "🧼 Personel Hijyen", 
            "🧹 Temizlik Kontrol",
            "📊 Kurumsal Raporlama", 
            "⚙️ Ayarlar"
        ])
        st.markdown("---")
        if st.button("Çıkış Yap"): 
            st.session_state.logged_in = False
            st.rerun()

    # >>> MODÜL 1: ÜRETİM GİRİŞİ <<<
    if menu == "🏭 Üretim Girişi":
        # Yetki kontrolü
        if not kullanici_yetkisi_var_mi(menu, "Düzenle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.info("💡 Yetki almak için sistem yöneticinize başvurun.")
            st.stop()
        
        st.title("🏭 Üretim Veri Girişi")
        u_df = veri_getir("Ayarlar_Urunler")
        
        if not u_df.empty:
            u_df.columns = [c.lower() for c in u_df.columns]
            # Bölüm Sorumlusu için ürün filtreleme
            u_df = bolum_bazli_urun_filtrele(u_df)
            
            if not u_df.empty:
                with st.form("uretim_form"):
                    col1, col2 = st.columns(2)
                    tarih = col1.date_input("Tarih", get_istanbul_time())
                    vardiya = col1.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"])
                    urun = col1.selectbox("Ürün", u_df['urun_adi'].unique()) 
                    lot_no = col2.text_input("Lot No")
                    miktar = col2.number_input("Miktar", min_value=1)
                    fire = col2.number_input("Fire", min_value=0)
                    notlar = col2.text_input("Notlar")
                    
                    if st.form_submit_button("💾 Kaydı Onayla"):
                        if lot_no:
                            yeni_kayit = [str(tarih), vardiya, st.session_state.user, "URETIM", urun, lot_no, miktar, fire, notlar, str(datetime.now())]
                            if guvenli_kayit_ekle("Depo_Giris_Kayitlari", yeni_kayit):
                                st.success("Kaydedildi!"); time.sleep(1); st.rerun()
                        else: st.warning("Lot No Giriniz!")
            
            st.divider()
            st.subheader("📊 Üretim Özeti")
            
            # Tarih filtresi
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_date = st.date_input("Tarih Seçin", value=get_istanbul_time().date(), key="prod_filter_date")
            
            # Kayıtları çek ve filtrele
            all_records = veri_getir("Depo_Giris_Kayitlari")
            
            if not all_records.empty:
                # Tarih kolonunu datetime'a çevir
                all_records['tarih'] = pd.to_datetime(all_records['tarih'])
                
                # Seçilen güne göre filtrele
                daily_records = all_records[all_records['tarih'].dt.date == filter_date]
                
                # Sütun isimlerini kontrol et (veritabanında farklı olabilir)
                groupby_cols = []
                if 'personel' in daily_records.columns:
                    groupby_cols.append('personel')
                elif 'kayit_eden' in daily_records.columns:
                    groupby_cols.append('kayit_eden')
                    
                if 'urun' in daily_records.columns:
                    groupby_cols.append('urun')
                elif 'urun_adi' in daily_records.columns:
                    groupby_cols.append('urun_adi')
                
                if not daily_records.empty and len(groupby_cols) > 0 and 'miktar' in daily_records.columns:
                    # Özet: Grup kolonlarına göre
                    agg_dict = {'miktar': 'sum'}
                    if 'fire' in daily_records.columns:
                        agg_dict['fire'] = 'sum'
                    
                    summary = daily_records.groupby(groupby_cols).agg(agg_dict).reset_index()
                    
                    # Sütun isimlerini yeniden adlandır
                    new_cols = ['Kayıt Eden', 'Ürün'] if len(groupby_cols) == 2 else [groupby_cols[0].title()]
                    new_cols.append('Toplam Miktar')
                    if 'fire' in agg_dict:
                        new_cols.append('Toplam Fire')
                    summary.columns = new_cols
                    
                    st.caption(f"📅 {filter_date} Tarihli Üretim Özeti")
                    st.dataframe(summary, use_container_width=True, hide_index=True)
                    
                    # Genel toplam
                    col_sum1, col_sum2, col_sum3 = st.columns(3)
                    with col_sum1:
                        st.metric("🏭 Toplam Üretim", f"{summary['Toplam Miktar'].sum():,.0f}")
                    with col_sum2:
                        fire_sum = summary.get('Toplam Fire', pd.Series([0])).sum()
                        st.metric("🔥 Toplam Fire", f"{fire_sum:,.0f}")
                    with col_sum3:
                        fire_sum = summary.get('Toplam Fire', pd.Series([0])).sum()
                        net = summary['Toplam Miktar'].sum() - fire_sum
                        st.metric("✅ Net Üretim", f"{net:,.0f}")
                elif not daily_records.empty:
                    st.warning("⚠️ Veri yapısı beklenenden farklı. Sütunlar: " + ", ".join(daily_records.columns.tolist()))
                else:
                    st.info(f"🔍 {filter_date} tarihinde üretim kaydı bulunamadı.")
            
            st.divider()
            st.subheader("📋 Son Kayıtlar (Detay)")
            st.dataframe(veri_getir("Depo_Giris_Kayitlari"), use_container_width=True)

        else: st.warning("Ürün tanımlı değil. Veri yükleme scriptini çalıştırın.")

    # >>> MODÜL 2: KPI & KALİTE KONTROL <<<
    elif menu == "🍩 KPI & Kalite Kontrol":
        # Yetki kontrolü
        if not kullanici_yetkisi_var_mi(menu, "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.stop()
        
        st.title("🍩 Dinamik Kalite Kontrol")
        u_df = veri_getir("Ayarlar_Urunler")
        if not u_df.empty:
            u_df.columns = [c.lower() for c in u_df.columns]
            # Bölüm Sorumlusu için ürün filtreleme
            u_df = bolum_bazli_urun_filtrele(u_df)
            
            c1, c2 = st.columns(2)
            u_df.columns = [c.lower() for c in u_df.columns] # Sütun isimlerini küçük harfe zorlar
            urun_secilen = c1.selectbox("Ürün Seçin", u_df['urun_adi'].unique())
            lot_kpi = c2.text_input("Lot No", placeholder="Üretim Lot No")
            vardiya_kpi = c1.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], key="kpi_v")
            
            urun_ayar = u_df[u_df['urun_adi'] == urun_secilen].iloc[0]
            
            # --- DİNAMİK YAPILANDIRMA ---
            numune_adet = int(urun_ayar.get('numune_sayisi', 1))
            if numune_adet < 1: numune_adet = 1
            
            # Parametreleri Çek
            params_sql = text("SELECT * FROM urun_parametreleri WHERE urun_adi = :u")
            try:
                params_df = pd.read_sql(params_sql, engine, params={"u": urun_secilen})
            except Exception as e:
                params_df = pd.DataFrame()

            if params_df.empty:
                # Eğer parametre yoksa eski usül (varsayılan) 3 ölçüm varsayalım
                param_list = [
                    {"parametre_adi": urun_ayar.get('olcum1_ad','Ölçüm 1')},
                    {"parametre_adi": urun_ayar.get('olcum2_ad','Ölçüm 2')},
                    {"parametre_adi": urun_ayar.get('olcum3_ad','Ölçüm 3')}
                ]
            else:
                param_list = params_df.to_dict('records')

            raf_omru = int(urun_ayar.get('raf_omru_gun', 0) or 0)
            stt_date = get_istanbul_time().date() + timedelta(days=raf_omru)
            st.info(f"ℹ {urun_secilen} için Raf Ömrü: {raf_omru} Gün | STT: {stt_date} | Numune Sayısı: {numune_adet}")

            with st.form("kpi_form"):
                # 1. STT ve Etiket Kontrolü (Zorunlu)
                st.subheader("✅ Ön Kontroller")
                stt_ok = st.checkbox("Üretim Tarihi ve Son Tüketim Tarihi (STT) Etiket Bilgisi Doğrudur")
                
                st.divider()
                st.subheader(f"📏 Ölçüm Değerleri ({numune_adet} Numune)")
                
                # Veri Toplama Havuzu
                all_measurements = [] # Her numune için bir dict saklayacağız
                
                # Dinamik Input Döngüsü
                # Cols yapısı: Her numune bir satır (row) olsun
                for i in range(numune_adet):
                     with st.container():
                        st.markdown(f"**Numune #{i+1}**")
                        cols = st.columns(len(param_list))
                        sample_data = {}
                        
                        for p_idx, param in enumerate(param_list):
                            p_ad = param['parametre_adi']
                            if p_ad: # Boş değilse
                                val = cols[p_idx % len(cols)].number_input(
                                    f"{p_ad}", 
                                    key=f"n{i}_p{p_idx}", 
                                    step=0.1,
                                    min_value=0.0
                                )
                                sample_data[p_ad] = val
                        
                        all_measurements.append(sample_data)
                        st.markdown("---")

                st.subheader("Duyusal Kontrol & Sonuç")
                d1, d2 = st.columns(2)
                tat = d1.selectbox("Tat / Koku", ["Uygun", "Uygun Değil"])
                goruntu = d2.selectbox("Görüntü / Renk", ["Uygun", "Uygun Değil"])
                not_kpi = st.text_area("Kalite Notu / Açıklama")
                
                if st.form_submit_button("✅ Analizi Kaydet"):
                    if not stt_ok:
                        st.error("⛔ Kayıt için STT ve Etiket bilgisini doğrulamalısınız!")
                    else:
                        try:
                            # Karar Mantığı
                            karar = "RED"
                            if tat == "Uygun" and goruntu == "Uygun":
                                karar = "ONAY"
                            
                            # İstatistik Hesapla (İlk 3 parametre için ortalama alıp eski sütunlara basalım)
                            # Bu sayede eski raporlar bozulmaz
                            avg_val1, avg_val2, avg_val3 = 0.0, 0.0, 0.0
                            
                            if len(param_list) > 0:
                                p1_name = param_list[0]['parametre_adi']
                                if p1_name: avg_val1 = sum([m.get(p1_name, 0) for m in all_measurements]) / numune_adet
                            
                            if len(param_list) > 1:
                                p2_name = param_list[1]['parametre_adi']
                                if p2_name: avg_val2 = sum([m.get(p2_name, 0) for m in all_measurements]) / numune_adet

                            if len(param_list) > 2:
                                p3_name = param_list[2]['parametre_adi']
                                if p3_name: avg_val3 = sum([m.get(p3_name, 0) for m in all_measurements]) / numune_adet

                            # Detaylı JSON/String Hazırla
                            detay_str = f"STT Onaylandı. "
                            for idx, m in enumerate(all_measurements):
                                detay_str += f"[N{idx+1}: " + ", ".join([f"{k}={v}" for k,v in m.items()]) + "] "
                            
                            # Not alanına ekle
                            final_not = f"{not_kpi} | {detay_str}"

                            simdi = get_istanbul_time()
                            veri_paketi = [
                                str(simdi.date()),              # 0
                                simdi.strftime("%H:%M"),        # 1
                                vardiya_kpi,                    # 2
                                urun_secilen,                   # 3
                                "",                             # 4
                                lot_kpi,                        # 5
                                str(stt_date),                  # 6
                                str(numune_adet),               # 7 (Numune No yerine Adedi yazalım)
                                avg_val1, avg_val2, avg_val3,   # 8, 9, 10 (Ortalamalar)
                                karar,                          # 11
                                st.session_state.user,          # 12
                                str(simdi),                     # 13
                                "", "",                         # 14, 15
                                tat,                            # 16
                                goruntu,                        # 17
                                final_not                       # 18 (Detaylı Veri)
                            ]
                            
                            if guvenli_kayit_ekle("Urun_KPI_Kontrol", veri_paketi):
                                st.success(f"✅ Analiz kaydedildi. Karar: {karar}")
                                st.caption("Detaylı veriler başarıyla işlendi.")
                                time.sleep(1.5); st.rerun()
                            else:
                                st.error("❌ Kayıt sırasında veritabanı hatası oluştu.")
                                
                        except Exception as e:
                            st.error(f"Beklenmeyen bir hata oluştu: {str(e)}")


    # >>> MODÜL: GMP DENETİMİ <<<
    elif menu == "🛡️ GMP Denetimi":
        # Yetki kontrolü
        if not kullanici_yetkisi_var_mi(menu, "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.stop()
        
        st.title("🛡️ GMP DENETİMİ")
        
        # 1. Frekans Algoritması
        simdi = get_istanbul_time()
        gun_index = simdi.weekday() # 0=Pazartesi
        ay_gunu = simdi.day
        
        aktif_frekanslar = ["GÜNLÜK"]
        if gun_index == 0: aktif_frekanslar.append("HAFTALIK") # Pazartesi haftalıkları da getir
        if ay_gunu == 1: aktif_frekanslar.append("AYLIK") # Ayın 1'i aylıkları da getir
        
        st.caption(f"📅 Bugünün Frekansı: {', '.join(aktif_frekanslar)}")

        try:
            # Lokasyonları ve Soruları Çek (Merkezi sistem: tanim_bolumler kullanıyoruz) - CACHED
            lok_df = veri_getir("Tanim_Bolumler")
            
            if not lok_df.empty:
                # Sütun ismi uyumu (id ve bolum_adi)
                lok_df = lok_df.rename(columns={'bolum_adi': 'lokasyon_adi'})
                
                selected_lok_id = st.selectbox("Denetim Yapılan Bölüm", 
                                             options=lok_df['id'].tolist(),
                                             format_func=lambda x: lok_df[lok_df['id']==x]['lokasyon_adi'].values[0],
                                             key="gmp_lok_main")
                
                # Soru havuzunu frekansa VE lokasyona göre filtrele
                frekans_filtre = "','".join(aktif_frekanslar)
                
                # LOKASYON FİLTRESİ: 
                # 1. lokasyon_ids NULL olanlar (tüm lokasyonlar)
                # 2. VEYA lokasyon_ids içinde seçili lokasyon ID'si geçenler
                soru_sql = f"""
                    SELECT * FROM gmp_soru_havuzu 
                    WHERE frekans IN ('{frekans_filtre}') 
                    AND aktif=TRUE
                    AND (
                        lokasyon_ids IS NULL 
                        OR ',' || lokasyon_ids || ',' LIKE '%,{selected_lok_id},%'
                    )
                """
                # CACHED QUERY
                soru_df = run_query(soru_sql)
                
                if soru_df.empty:
                    st.warning(f"⚠️ {lok_df[lok_df['id']==selected_lok_id]['lokasyon_adi'].values[0]} için bugün ({', '.join(aktif_frekanslar)}) sorulacak soru bulunmuyor.")

                    st.info("💡 İpucu: Ayarlar → GMP Sorular bölümünden yeni sorular ekleyin ve lokasyon seçimini yapın.")
                else:
                    with st.form("gmp_denetim_formu"):
                        st.subheader(f"📍 {lok_df[lok_df['id']==selected_lok_id]['lokasyon_adi'].values[0]} Denetim Soruları")
                        
                        denetim_verileri = []
                        
                        for idx, soru in soru_df.iterrows():
                            with st.container(border=True):
                                c1, c2 = st.columns([3, 1])
                                c1.markdown(f"**{soru['soru_metni']}**")
                                c1.caption(f"🏷️ Kategori: {soru['kategori']} | 📑 BRC Ref: {soru['brc_ref']} | ⚡ Risk: {soru['risk_puani']}")
                                
                                # Key hatasını önlemek için soru ID'si yoksa index kullan
                                q_key_id = soru['id'] if pd.notna(soru['id']) else f"idx_{idx}"
                                durum = c2.radio("Durum", ["UYGUN", "UYGUN DEĞİL"], key=f"gmp_q_{selected_lok_id}_{q_key_id}", horizontal=True)
                                
                                # Risk 3 Mantığı: Uygun değilse zorunlu alanlar
                                foto = None
                                notlar = ""
                                if durum == "UYGUN DEĞİL":
                                    if soru['risk_puani'] == 3:
                                        st.warning("🚨 KRİTİK BULGU! Fotoğraf ve açıklama zorunludur.")
                                        foto = st.file_uploader("⚠️ Fotoğraf Çek/Yükle", type=['jpg','png','jpeg'], key=f"foto_{selected_lok_id}_{soru['id']}")
                                    
                                    notlar = st.text_area("Hata Açıklaması / Düzeltici Faaliyet", key=f"not_{selected_lok_id}_{soru['id']}")

                                denetim_verileri.append({
                                    "soru_id": soru['id'],
                                    "durum": durum,
                                    "foto": foto,
                                    "notlar": notlar,
                                    "risk": soru['risk_puani'],
                                    "brc": soru['brc_ref']
                                })
                        
                        if st.form_submit_button("✅ Denetimi Tamamla ve Gönder"):
                            hata_var = False
                            for d in denetim_verileri:
                                if d['durum'] == "UYGUN DEĞİL" and d['risk'] == 3 and not d['foto']:
                                    st.error(f"Kritik sorularda fotoğraf zorunludur! (BRC: {d['brc']})")
                                    hata_var = True
                                    break
                            
                            if not hata_var:
                                try:
                                    with engine.connect() as conn:
                                        for d in denetim_verileri:
                                            # Fotoğraf kaydetme simülasyonu (dosya ismini DB'ye yazıyoruz)
                                            foto_adi = f"gmp_{simdi.strftime('%Y%m%d_%H%M%S')}_{d['soru_id']}.jpg" if d['foto'] else None
                                            
                                            sql = """INSERT INTO gmp_denetim_kayitlari 
                                                     (tarih, saat, kullanici, lokasyon_id, soru_id, durum, fotograf_yolu, notlar, brc_ref, risk_puani)
                                                     VALUES (:t, :s, :k, :l, :q, :d, :f, :n, :b, :r)"""
                                            params = {
                                                "t": str(simdi.date()), "s": simdi.strftime("%H:%M"), "k": st.session_state.user,
                                                "l": selected_lok_id, "q": d['soru_id'], "d": d['durum'], "f": foto_adi,
                                                "n": d['notlar'], "b": d['brc'], "r": d['risk']
                                            }
                                            conn.execute(text(sql), params)
                                        conn.commit()
                                    st.success("✅ Denetim başarıyla kaydedildi!"); time.sleep(1.5); st.rerun()
                                except Exception as e:
                                    st.error(f"Kaydetme hatası: {e}")
            else:
                st.warning("⚠️ Henüz Bölüm veya Soru tanımlanmamış.")
                st.info("💡 Lütfen önce Ayarlar → Temizlik & Bölümler kısmından fabrika bölümlerini tanımlayın, ardından GMP Sorular kısmından soru ekleyin.")
        except Exception as e:
            st.error(f"Sistem Hatası: {e}")

    # >>> MODÜL 3: PERSONEL HİJYEN <<<
    elif menu == "🧼 Personel Hijyen":
        # Yetki kontrolü
        if not kullanici_yetkisi_var_mi(menu, "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.stop()
        
        st.title("⚡ Akıllı Personel Kontrol Paneli")
        
        # 1. Personel Listesini SQLite'dan Çek
        p_list = pd.read_sql("""
            SELECT p.ad_soyad, 
                   COALESCE(d.bolum_adi, 'Tanımsız') as bolum, 
                   p.vardiya, 
                   p.durum 
            FROM personel p
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
            WHERE p.ad_soyad IS NOT NULL
        """, engine)
        p_list.columns = ["Ad_Soyad", "Bolum", "Vardiya", "Durum"] # Kodun beklediği büyük harf formatına çevirir
        
        if not p_list.empty:
            # Temizlik ve Filtreleme
            p_list = p_list[p_list['Durum'].astype(str) == "AKTİF"]
            
            c1, c2 = st.columns(2)
            # Filter out NaN/None values and convert to list before sorting
            vardiya_values = [v for v in p_list['Vardiya'].unique() if pd.notna(v)]
            v_sec = c1.selectbox("Vardiya Seçiniz", sorted(vardiya_values) if vardiya_values else ["GÜNDÜZ VARDİYASI"])
            p_v = p_list[p_list['Vardiya'] == v_sec]
            
            if not p_v.empty:
                bolum_values = [b for b in p_v['Bolum'].unique() if pd.notna(b)]
                b_sec = c2.selectbox("Bölüm Seçiniz", sorted(bolum_values) if bolum_values else ["Tanımsız"])
                p_b = p_v[p_v['Bolum'] == b_sec]
                
                if not p_b.empty:
                    personel_isimleri = sorted(p_b['Ad_Soyad'].unique())
                    
                    # Session State'de Tablo Verisini Tutalım
                    if 'hijyen_tablo' not in st.session_state or st.session_state.get('son_bolum') != b_sec:
                         st.session_state.hijyen_tablo = pd.DataFrame({
                            "Personel Adı": personel_isimleri,
                            "Durum": "Sorun Yok"
                        })
                         st.session_state.son_bolum = b_sec

                    # --- TANIMLAMALAR ---
                    sebepler = {
                        "Gelmedi": ["Seçiniz...", "Yıllık İzin", "Raporlu", "Habersiz Gelmedi", "Ücretsiz İzin"],
                        "Sağlık Riski": ["Seçiniz...", "Ateş", "İshal", "Öksürük", "Açık Yara", "Bulaşıcı Şüphe"],
                        "Hijyen Uygunsuzluk": ["Seçiniz...", "Kirli Önlük", "Sakal Tıraşı", "Bone/Maske Eksik", "Yasaklı Takı"]
                    }
                    aksiyonlar = {
                        "Gelmedi": ["İK Bilgilendirildi", "Tutanak Tutuldu", "Bilgi Dahilinde"],
                        "Sağlık Riski": ["Üretim Md. Bilgi Verildi", "Eve Gönderildi", "Revire Yönlendirildi", "Maskeli Çalışıyor"],
                        "Hijyen Uygunsuzluk": ["Personel Uyarıldı", "Uygunsuzluk Giderildi", "Eğitim Verildi"]
                    }

                    # --- 2. ANA TABLO (HIZLI SEÇİM) ---
                    df_sonuc = st.data_editor(
                        st.session_state.hijyen_tablo,
                        column_config={
                            "Personel Adı": st.column_config.TextColumn("Personel", disabled=True),
                            "Durum": st.column_config.SelectboxColumn(
                                "Durum Seçin",
                                options=["Sorun Yok", "Gelmedi", "Sağlık Riski", "Hijyen Uygunsuzluk"],
                                required=True
                            )
                        },
                        hide_index=True,
                        key=f"editor_{b_sec}",
                        use_container_width=True
                    )

                    # --- 3. DİNAMİK DETAYLAR ---
                    sorunlu_personel = df_sonuc[df_sonuc["Durum"] != "Sorun Yok"]
                    detaylar_dict = {}

                    if not sorunlu_personel.empty:
                        st.divider()
                        st.subheader("📝 Tespit Detayı ve Aksiyon")
                        cols = st.columns(3)
                        
                        for i, (idx, row) in enumerate(sorunlu_personel.iterrows()):
                            p_adi = row["Personel Adı"]
                            p_durum = row["Durum"]
                            
                            with cols[i % 3]:
                                with st.container(border=True):
                                    st.write(f"**{p_adi}**")
                                    sebep = st.selectbox(f"Neden?", sebepler[p_durum], key=f"s_{p_adi}")
                                    aksiyon = st.selectbox(f"Aksiyon?", aksiyonlar[p_durum], key=f"a_{p_adi}")
                                    detaylar_dict[p_adi] = {"sebep": sebep, "aksiyon": aksiyon}

                    # --- 4. KAYDET (SQLite) ---
                    if st.button(f"💾 {b_sec} DENETİMİNİ KAYDET", type="primary", use_container_width=True):
                        kayit_listesi = []
                        valid = True
                        
                        for _, row in df_sonuc.iterrows():
                            p_adi = row["Personel Adı"]
                            p_durum = row["Durum"]
                            sebep, aksiyon = "-", "-"
                            
                            if p_durum != "Sorun Yok":
                                det = detaylar_dict.get(p_adi)
                                if det and "Seçiniz" not in det["sebep"]:
                                    sebep, aksiyon = det["sebep"], det["aksiyon"]
                                else:
                                    valid = False; break
                            
                            kayit_listesi.append({
                                "tarih": str(get_istanbul_time().date()),
                                "saat": get_istanbul_time().strftime("%H:%M"),
                                "kullanici": st.session_state.user,
                                "vardiya": v_sec, "bolum": b_sec,
                                "personel": p_adi, "durum": p_durum,
                                "sebep": sebep, "aksiyon": aksiyon
                            })
                        
                        if valid:
                            pd.DataFrame(kayit_listesi).to_sql("hijyen_kontrol_kayitlari", engine, if_exists='append', index=False)
                            st.success("✅ Veritabanına kaydedildi!"); time.sleep(1); st.rerun()
                        else: st.error("Lütfen tüm detayları seçiniz!")
                else: st.warning("Bu bölümde personel bulunamadı.")
            else: st.warning("Bu vardiyada personel bulunamadı.")
        else: st.warning("Sistemde aktif personel bulunamadı.")
    # >>> MODÜL: TEMİZLİK VE SANİTASYON <<<
    elif menu == "🧹 Temizlik Kontrol":
        # Yetki kontrolü
        if not kullanici_yetkisi_var_mi(menu, "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.stop()
        
        st.title("🧹 Temizlik ve Sanitasyon Yönetimi")
        tab_uygulama, tab_master_plan = st.tabs(["📋 Saha Uygulama Çizelgesi", "⚙️ Master Plan Düzenleme"])

        with tab_uygulama:
            try:
                plan_df = veri_getir("Ayarlar_Temizlik_Plani")
                if not plan_df.empty:
                    c1, c2 = st.columns(2)
                    kat_listesi = sorted(plan_df['kat_bolum'].unique())
                    secili_kat = c1.selectbox("Denetlenecek Kat / Bölüm", kat_listesi, key="clean_kat_select")
                    vardiya = c2.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], key="t_v_apply")
                    isler = plan_df[plan_df['kat_bolum'] == secili_kat]
                    
                    st.info(f"💡 {secili_kat} için {len(isler)} adet temizlik görevi listelendi.")

                    # YETKİ KONTROLÜ
                    # Sadece Admin, Kalite, Vardiya Amiri ve Emre ÇAVDAR kayıt girebilir
                    is_controller = (st.session_state.user in CONTROLLER_ROLES) or (st.session_state.user in ADMIN_USERS)
                    
                    if not is_controller:
                        st.warning(f"⚠️ {st.session_state.user}, bu alanda sadece Görüntüleme yetkiniz var. Müdahale edemezsiniz.")

                    with st.form("temizlik_kayit_formu"):
                        kayitlar = []
                        h1, h2, h3, h4 = st.columns([3, 2, 2, 2])
                        h1.caption("📍 Ekipman / Alan"); h2.caption("🧪 Kimyasal / Sıklık"); h3.caption("❓ Durum"); h4.caption("🔍 Doğrulama / Not")
                        st.markdown("---")
                        
                        for idx, row in isler.iterrows():
                            r1, r2, r3, r4 = st.columns([3, 2, 2, 2])
                            r1.write(f"**{row['yer_ekipman']}** \n ({row['risk']})")
                            r2.caption(f"{row['kimyasal']} \n {row['siklik']}")
                            with st.expander("ℹ️ Detaylar ve Yöntem"):
                                st.markdown(f"**Uygulama Yöntemi:** {row.get('uygulama_yontemi', '-')}")
                                st.info(f"🧬 **Validasyon:** {row.get('validasyon_siklik', '-')} | **Verifikasyon:** {row.get('verifikasyon', '-')} ({row.get('verifikasyon_siklik', '-')})")
                                st.caption(f"**Sorumlu:** {row.get('uygulayici', '-')} | **Kontrol:** {row.get('kontrol_eden', '-')} | **Kayıt No:** {row.get('kayit_no', '-')}")

                            # Durum Seçimi (Yetkisiz ise Disabled)
                            durum_key = f"d_{idx}"
                            durum = r3.selectbox(
                                "Seç", ["TAMAMLANDI", "YAPILMADI"], 
                                key=durum_key, 
                                label_visibility="collapsed",
                                disabled=not is_controller
                            )
                            
                            val_not = ""
                            if durum == "TAMAMLANDI":
                                # Verifikasyon Kontrolü (ATP vb.)
                                verify_method = row.get('verifikasyon')
                                if verify_method and verify_method not in ['-', '']:
                                    r4.info(f"🧬 **{verify_method}**")
                                    # Kontrolör ise sonuç girebilir
                                    val_not = r4.text_input(
                                        f"{verify_method} Sonuç/RLU", 
                                        placeholder="Sonuç giriniz...", 
                                        key=f"v_res_{idx}",
                                        disabled=not is_controller
                                    )
                                else:
                                    val_not = r4.text_input("Not", key=f"v_note_{idx}", label_visibility="collapsed", disabled=not is_controller)
                            else:
                                val_not = r4.selectbox(
                                    "Neden?", ["Seçiniz...", "Arıza", "Malzeme Eksik", "Zaman Yetersiz"], 
                                    key=f"v_why_{idx}", 
                                    label_visibility="collapsed",
                                    disabled=not is_controller
                                )
                            
                            # Sadece yetkili kişi işlem yapınca listeye ekle
                            # Sadece yetkili kişi işlem yapınca listeye ekle
                            if is_controller:
                                kayitlar.append({
                                    "tarih": str(get_istanbul_time().date()), 
                                    "saat": get_istanbul_time().strftime("%H:%M"),
                                    "kullanici": st.session_state.user, "bolum": secili_kat,
                                    "islem": row['yer_ekipman'], "durum": durum, "aciklama": val_not
                                })
                        
                        if st.form_submit_button("💾 TÜM KAYITLARI VERİTABANINA İŞLE", use_container_width=True):
                            pd.DataFrame(kayitlar).to_sql("temizlik_kayitlari", engine, if_exists='append', index=False)
                            st.success(f"✅ {secili_kat} temizlik kayıtları kaydedildi!"); time.sleep(1); st.rerun()
                else:
                    st.warning("Veritabanında kayıtlı temizlik planı bulunamadı.")
            except Exception as e:
                st.error(f"Saha formu yüklenirken hata oluştu: {e}")

        with tab_master_plan:
            st.subheader("⚙️ Master Temizlik Planı Editörü")
            try:
                # Tüm lokasyonları çek (hiyerarşi için)
                lok_df = pd.read_sql("SELECT id, ad, tip, parent_id FROM lokasyonlar WHERE aktif=TRUE ORDER BY tip, ad", engine)
                
                # Kat listesi
                lst_kat = lok_df[lok_df['tip'] == 'Kat']['ad'].tolist()
                if not lst_kat: lst_kat = ["Tanımsız"]
                
                # --- DİNAMİK FİLTRELEME: Kat seçimine göre Bölüm ve Ekipman listesi ---
                st.caption("🔍 Yeni kayıt eklerken filtre olarak kullanın:")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    filter_kat = st.selectbox("🏢 Kat Filtresi", ["(Tümü)"] + lst_kat, key="mp_filter_kat")
                
                # Bölüm listesini filtrele
                if filter_kat != "(Tümü)":
                    # Seçilen katın ID'sini bul
                    kat_id = lok_df[(lok_df['ad'] == filter_kat) & (lok_df['tip'] == 'Kat')]['id'].values
                    if len(kat_id) > 0:
                        kat_id = kat_id[0]
                        # Bu kata bağlı bölümler
                        lst_bolum = lok_df[(lok_df['tip'] == 'Bölüm') & (lok_df['parent_id'] == kat_id)]['ad'].tolist()
                        # Bu bölümlere bağlı ekipmanlar
                        bolum_ids = lok_df[(lok_df['tip'] == 'Bölüm') & (lok_df['parent_id'] == kat_id)]['id'].tolist()
                        lst_ekipman = lok_df[(lok_df['tip'] == 'Ekipman') & (lok_df['parent_id'].isin(bolum_ids))]['ad'].tolist()
                    else:
                        lst_bolum = lok_df[lok_df['tip'] == 'Bölüm']['ad'].tolist()
                        lst_ekipman = lok_df[lok_df['tip'] == 'Ekipman']['ad'].tolist()
                else:
                    lst_bolum = lok_df[lok_df['tip'] == 'Bölüm']['ad'].tolist()
                    lst_ekipman = lok_df[lok_df['tip'] == 'Ekipman']['ad'].tolist()
                
                if not lst_bolum: lst_bolum = ["Tanımsız"]
                if not lst_ekipman: lst_ekipman = ["Tanımsız"]
                
                with col_f2:
                    st.info(f"📊 {len(lst_bolum)} bölüm, {len(lst_ekipman)} ekipman listelendi")
                
                try: 
                    kim_df = veri_getir("Kimyasal_Envanter")
                    lst_kimyasal = kim_df['kimyasal_adi'].tolist() if not kim_df.empty else []
                except: lst_kimyasal = []
                
                try: 
                    met_df = veri_getir("Tanim_Metotlar")
                    lst_metot = met_df['metot_adi'].tolist() if not met_df.empty else []
                except: lst_metot = []

                # --- YENİ EKLENEN PERSONEL LİSTELERİ ---
                # 1. Uygulayıcılar: Görevi 'Temizlik' veya 'Ekip Üyesi' olanlar (Büyük/Küçük harf uyumu için LIKE kullanıyoruz)
                try:
                    sql_uyg = """SELECT ad_soyad FROM personel 
                                 WHERE (gorev LIKE '%Temizlik%' OR gorev LIKE '%TEMİZLİK%' OR gorev LIKE '%Ekip%' OR gorev LIKE '%EKİP%') 
                                 AND durum='AKTİF' AND ad_soyad IS NOT NULL"""
                    lst_uygulayici = pd.read_sql(sql_uyg, engine)['ad_soyad'].tolist()
                    if not lst_uygulayici: lst_uygulayici = ["Tanımsız"]
                except: lst_uygulayici = ["Tanımsız"]

                # 2. Kontrol Edenler: Sistem Kullanıcısı Olanlar (Admin, Kalite vb.)
                # Ad Soyad yoksa Kullanıcı Adını al
                try:
                    sql_kon = "SELECT COALESCE(ad_soyad, kullanici_adi) as isim FROM personel WHERE kullanici_adi IS NOT NULL"
                    lst_kontrolor = pd.read_sql(sql_kon, engine)['isim'].tolist()
                    if not lst_kontrolor: lst_kontrolor = ["Tanımsız"]
                except: lst_kontrolor = ["Tanımsız"]

                master_df = pd.read_sql("SELECT * FROM ayarlar_temizlik_plani", engine)
                
                # Sütun Sıralaması: Kat sütununu en başa al
                if 'kat' in master_df.columns:
                    cols = ['kat'] + [c for c in master_df.columns if c != 'kat']
                    master_df = master_df[cols]

                # Düzenlenebilir tablo (Data Editor)
                edited_df = st.data_editor(
                    master_df, 
                    num_rows="dynamic", 
                    use_container_width=True, 
                    hide_index=True,
                    key="master_plan_editor_main",
                    column_config={
                        "kat": st.column_config.SelectboxColumn("🏢 Kat", options=lst_kat, required=True),
                        "kat_bolum": st.column_config.SelectboxColumn("🏭 Bölüm", options=lst_bolum, required=True),
                        "yer_ekipman": st.column_config.SelectboxColumn("⚙️ Ekipman", options=lst_ekipman, required=True),
                        "kimyasal": st.column_config.SelectboxColumn("Kimyasal", options=lst_kimyasal),
                        "uygulama_yontemi": st.column_config.SelectboxColumn("Yöntem", options=lst_metot),
                        "uygulayici": st.column_config.SelectboxColumn("Uygulayıcı Personel", options=lst_uygulayici),
                        "kontrol_eden": st.column_config.SelectboxColumn("Kontrol Eden", options=lst_kontrolor),
                        "validasyon_siklik": st.column_config.SelectboxColumn(
                            "Validasyon Sıklığı", options=["Her Yıkama", "Günlük", "Haftalık", "Aylık", "Periyodik"]
                        ),
                        "verifikasyon": st.column_config.SelectboxColumn(
                            "Verifikasyon Yöntemi", options=["Görsel", "ATP", "Swap", "Allerjen Kit", "Mikrobiyolojik"]
                        ),
                        "verifikasyon_siklik": st.column_config.SelectboxColumn(
                            "Verifikasyon Sıklığı", options=["Her Yıkama", "Günlük", "Haftalık", "Aylık", "Rastgele", "3 Aylık"]
                        ),
                        "risk": st.column_config.SelectboxColumn("Risk Seviyesi", options=["Yüksek", "Orta", "Düşük"])
                    }
                )
                if st.button("💾 Master Planı Güncelle", type="primary", use_container_width=True):
                    # Cache Temizle
                    cached_veri_getir.clear()
                    get_department_hierarchy.clear()
                    
                    edited_df.to_sql("ayarlar_temizlik_plani", engine, if_exists='replace', index=False)
                    st.success("✅ Master Plan Güncellendi!"); time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"Master plan yüklenirken hata oluştu: {e}")

    # >>> MODÜL: KURUMSAL RAPORLAMA <<<
    elif menu == "📊 Kurumsal Raporlama":
        # Yetki kontrolü
        if not kullanici_yetkisi_var_mi(menu, "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.stop()
        
        st.title("📊 Kurumsal Kalite ve Üretim Raporları")
        st.markdown("---")
        
        # Üst Filtre Paneli
        c1, c2, c3 = st.columns([1, 1, 1])
        bas_tarih = c1.date_input("Başlangıç Tarihi", get_istanbul_time() - timedelta(days=7))
        bit_tarih = c2.date_input("Bitiş Tarihi", get_istanbul_time())
        rapor_tipi = c3.selectbox("Rapor Kategorisi", [
            "🏭 Üretim ve Verimlilik", 
            "🍩 Kalite (KPI) Analizi", 
            "🧼 Personel Hijyen Özeti", 
            "🧹 Temizlik Takip Raporu",
            "📍 Kurumsal Lokasyon & Proses Haritası",
            "👥 Personel Organizasyon Şeması"
        ])
        
        # Organizasyon şeması için görünüm seçici (form içinde)
        gorunum_tipi = None
        if rapor_tipi == "👥 Personel Organizasyon Şeması":
            gorunum_tipi = st.radio(
                "📱 Görünüm Tipi",
                ["🖥️ İnteraktif Görünüm (Ekran)", "📄 PDF Çıktısı (Yazdırma)", "📋 Liste Formatı (A4 Yatay)"],
                horizontal=True,
                help="İnteraktif: Departman bazlı hiyerarşi | PDF: Görsel şema | Liste: Basit hiyerarşik liste"
            )

        if st.button("Raporu Oluştur", use_container_width=True):
            st.markdown(f"### 📋 {rapor_tipi}")
            
            # 1. ÜRETİM RAPORU
            if rapor_tipi == "🏭 Üretim ve Verimlilik":
                df = run_query(f"SELECT * FROM depo_giris_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
                if not df.empty:
                    # Özet Kartlar
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Toplam Üretim (Adet)", f"{df['miktar'].sum():,}")
                    k2.metric("Toplam Fire", f"{df['fire'].sum():,}")
                    fire_oran = (df['fire'].sum() / df['miktar'].sum()) * 100 if df['miktar'].sum() > 0 else 0
                    k3.metric("Ortalama Fire Oranı", f"%{fire_oran:.2f}")
                    
                    st.dataframe(df, use_container_width=True)
                else: st.warning("Bu tarihler arasında üretim kaydı bulunamadı.")

            # 2. KALİTE (KPI) ANALİZİ
            elif rapor_tipi == "🍩 Kalite (KPI) Analizi":
                df = run_query(f"SELECT * FROM urun_kpi_kontrol WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
                if not df.empty:
                    k1, k2 = st.columns(2)
                    onay_sayisi = len(df[df['karar'] == 'ONAY'])
                    red_sayisi = len(df[df['karar'] == 'RED'])
                    k1.success(f"✅ Onaylanan: {onay_sayisi}")
                    k2.error(f"❌ Reddedilen: {red_sayisi}")
                    
                    # Ürün bazlı red analizi
                    red_df = df[df['karar'] == 'RED'].groupby('urun').size().reset_index(name='Red Adeti')
                    if not red_df.empty:
                        st.write("🔔 **En Çok Red Alan Ürünler**")
                        st.table(red_df)
                    
                    st.dataframe(df, use_container_width=True)
                else: st.warning("Kalite kaydı bulunamadı.")

            # 3. PERSONEL HİJYEN ÖZETİ
            elif rapor_tipi == "🧼 Personel Hijyen Özeti":
                df = pd.read_sql(f"SELECT * FROM hijyen_kontrol_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'", engine)
                if not df.empty:
                    # 'Sorun Yok' haricindeki her şey bir uygunsuzluktur
                    uygunsuzluk = df[df['durum'] != 'Sorun Yok']
                    
                    if not uygunsuzluk.empty:
                        st.error(f"⚠️ Belirtilen tarihlerde {len(uygunsuzluk)} Personel Uygunsuzluğu / Devamsızlığı Tespit Edildi.")
                        st.write("🔍 **Uygunsuzluk Detayları (Tüm Detaylar)**")
                        # Tüm kolonları göster (Özellikle Sebep ve Aksiyon)
                        viz_cols = ['tarih', 'saat', 'personel', 'bolum', 'durum', 'sebep', 'aksiyon', 'vardiya']
                        present_cols = [c for c in viz_cols if c in uygunsuzluk.columns]
                        st.dataframe(uygunsuzluk[present_cols], use_container_width=True, hide_index=True)
                        
                        # Özet istatistik
                        st.divider()
                        st.write("📊 **Duruma Göre Dağılım**")
                        durum_ozet = uygunsuzluk['durum'].value_counts()
                        st.bar_chart(durum_ozet)
                    else:
                        st.success("✅ Seçilen tarih aralığında herhangi bir personel uygunsuzluğu bulunamadı.")
                    
                    with st.expander("📋 Tüm Kayıtları Göster (Sorunsuzlar Dahil)"):
                        st.dataframe(df, use_container_width=True, hide_index=True)
                else: 
                    st.warning("⚠️ Seçilen tarihlerde herhangi bir hijyen kaydı bulunamadı.")

            # 4. TEMİZLİK TAKİP RAPORU
            elif rapor_tipi == "🧹 Temizlik Takip Raporu":
                df = run_query(f"SELECT * FROM temizlik_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
                if not df.empty:
                    st.success(f"✅ Belirtilen tarihlerde {len(df)} temizlik görevi tamamlandı.")
                    bolum_bazli = df.groupby('bolum').size().reset_index(name='Tamamlanan İşlem')
                    st.bar_chart(bolum_bazli.set_index('bolum'))
                    st.dataframe(df, use_container_width=True)
                else: st.warning("Temizlik kaydı bulunamadı.")
            
            # 5. LOKASYON & PROSES HARİTASI (YENİ VE GELİŞMİŞ)
            elif rapor_tipi == "📍 Kurumsal Lokasyon & Proses Haritası":
                st.info("Bu harita, fabrikanın fiziksel yapısını (Kat > Bölüm > Hat > Ekipman) ve buralarda yürütülen prosesleri gösterir.")
                
                try:
                    # Gerekli Verileri Çek (Lokasyonlar, Proses Atamaları, Departmanlar)
                    loc_df = pd.read_sql("SELECT * FROM lokasyonlar WHERE aktif IS TRUE ORDER BY parent_id NULLS FIRST, id", engine)
                    
                    try:
                        proses_map = pd.read_sql("""
                            SELECT lpa.lokasyon_id, pt.ad as proses_adi, pt.ikon 
                            FROM lokasyon_proses_atama lpa 
                            JOIN proses_tipleri pt ON lpa.proses_tip_id = pt.id 
                            WHERE lpa.aktif IS TRUE
                        """, engine)
                    except:
                        proses_map = pd.DataFrame()
                        
                    if not loc_df.empty:
                        # GÖRÜNÜM SEÇENEĞİ
                        harita_tipi = st.radio(
                            "Görünüm Seçiniz:", 
                            ["📱 İnteraktif Harita (Genişletilebilir)", "📄 PDF Şeması (Tüm Fabrika)"], 
                            horizontal=True
                        )
                        
                        # ---------------------------------------------------------
                        # 1. İLİŞKİ AĞACINI OLUŞTUR (Ortak Logic)
                        # ---------------------------------------------------------
                        tree = {}
                        roots = []
                        all_ids = set(loc_df['id'].unique())
                        
                        for _, row in loc_df.iterrows():
                            # ID ve Parent ID'yi güvenli integer'a çevir
                            lid = int(row['id'])
                            pid = row['parent_id']
                            
                            # Parent ID NaN veya 0 ise None yap
                            if pd.isna(pid) or pid == 0 or pid == "":
                                pid = None
                            else:
                                try:
                                    pid = int(pid)
                                    if pid not in all_ids: pid = None
                                except: pid = None
                            
                            # Ağaca ekle
                            if pid is None:
                                roots.append(lid)
                            else:
                                if pid not in tree: tree[pid] = []
                                tree[pid].append(lid)

                        # =========================================================
                        # MOD A: İNTERAKTİF HARİTA (EXPANDER)
                        # =========================================================
                        if harita_tipi == "📱 İnteraktif Harita (Genişletilebilir)":
                            st.markdown("### 🏭 Fabrika Yerleşim Planı")
                            
                            # İstatistikler (Hızlı Bakış)
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Toplam Lokasyon", len(loc_df))
                            c2.metric("Aktif Bölüm", len(loc_df[loc_df['tip']=='Bölüm']))
                            c3.metric("Üretim Hattı", len(loc_df[loc_df['tip']=='Hat']))
                            c4.metric("Makine/Ekipman", len(loc_df[loc_df['tip']=='Ekipman']))
                            st.divider()

                            def render_interactive_location(loc_id, level=0):
                                """Lokasyonu ve çocuklarını recursive expander olarak çizer"""
                                try:
                                    loc_row = loc_df[loc_df['id'] == loc_id].iloc[0]
                                except: return
                                
                                l_ad = loc_row['ad']
                                l_tip = loc_row['tip']
                                
                                # İkon Seçimi
                                icon = "📍"
                                if l_tip == 'Kat': icon = "🏢"
                                elif l_tip == 'Bölüm': icon = "🏭"
                                elif l_tip == 'Hat': icon = "🛤️"
                                elif l_tip == 'Ekipman': icon = "⚙️"
                                
                                # Proses Bilgisi
                                proses_badges = ""
                                if not proses_map.empty:
                                    p_list = proses_map[proses_map['lokasyon_id'] == loc_id]
                                    for _, p in p_list.iterrows():
                                        if pd.notna(p['proses_adi']):
                                            p_icon = p.get('ikon', '🔧')
                                            # HTML badge
                                            proses_badges += f" <span style='background-color:#E8F8F5; color:#117864; padding:2px 6px; border-radius:4px; font-size:0.8em;'>{p_icon} {p['proses_adi']}</span>"
                                
                                # Çocukları var mı?
                                children = tree.get(loc_id, [])
                                
                                # Başlık Oluştur
                                title = f"{icon} **{l_ad}** <span style='color:grey; font-size:0.8em'>({l_tip})</span> {proses_badges}"
                                
                                # Girinti (Görsel Hiyerarşi)
                                margin_left = level * 20
                                
                                if children:
                                    # Alt birimi olanlar EXPANDER olur (Varsayılan: Katlar açık)
                                    is_expanded = (l_tip == 'Kat')
                                    # Expanderı biraz içeriden başlatmak için container kullanabiliriz ama st.expander margin kabul etmez.
                                    # O yüzden markdown ile hile yapacağız veya direkt basacağız.
                                    
                                    with st.expander(label=f"{icon} {l_ad} ({len(children)} alt birim) {l_tip}", expanded=is_expanded):
                                        # İçerik Detayı (Opsiyonel)
                                        if proses_badges:
                                            st.markdown(f"**Prosesler:** {proses_badges}", unsafe_allow_html=True)
                                            
                                        # Çocukları Recursive Çiz
                                        for child_id in children:
                                            render_interactive_location(child_id, level + 1)
                                else:
                                    # Alt birimi olmayanlar (Genelde Ekipmanlar)
                                    st.markdown(f"""
                                    <div style="
                                        margin-left: 20px;
                                        padding: 10px;
                                        border-left: 4px solid #FF4B4B; 
                                        background-color: #262730;
                                        color: #FAFAFA;
                                        margin-bottom: 6px;
                                        border-radius: 0 4px 4px 0;
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                                    ">
                                        {title}
                                    </div>
                                    """, unsafe_allow_html=True)

                            # Ana Döngü
                            if not roots:
                                st.warning("⚠️ Kök lokasyon bulunamadı. Lütfen Ayarlar > Lokasyonlar menüsünden en az bir 'Kat' tanımlayın.")
                            else:
                                for root_id in roots:
                                    render_interactive_location(root_id)
                        
                        # =========================================================
                        # MOD B: PDF ŞEMASI (GRAPHVIZ)
                        # =========================================================
                        else:
                            # Graphviz DOT Kodu Oluşturucu
                            dot = 'digraph FactoryMap {\n'
                            dot += '  compound=true;\n'
                            dot += '  rankdir=LR;\n' # Soldan Sağa Akış (Proses Akışı Gibi)
                            dot += '  splines=ortho;\n' # Köşeli çizgiler
                            dot += '  nodesep=0.4;\n'
                            dot += '  ranksep=1.2;\n'
                            
                            # Stil Tanımları
                            dot += '  node [shape=box, style="filled,rounded", fontname="Arial", fontsize=10, height=0.5];\n'
                            dot += '  edge [color="#5D6D7E", penwidth=1.2, arrowhead=vee];\n'
                            
                            # ---------------------------------------------------------
                            # RECURSIVE KÜMELEME (CLUSTER) FONKSİYONU
                            # ---------------------------------------------------------
                            # Lokasyonları iç içe kutular (subgraph cluster) olarak çizer
                            
                            # Graphviz'de cluster ID'leri 'cluster_' ile başlamak ZORUNDADIR.
                            # Node ID'leri ise sayı ile başlayamaz, harf eklemek gerekir.
                            
                            # 1. İlişki Ağacını Oluştur (Parent -> Children Map)
                            # tree ve roots zaten yukarıda oluşturuldu.
                            
                            def draw_location_recursive_dot(loc_id):
                                # Lokasyon detaylarını bul
                                try:
                                    loc_row = loc_df[loc_df['id'] == loc_id].iloc[0]
                                    l_ad = str(loc_row['ad']).replace('"', "'")
                                    l_tip = loc_row['tip']
                                except:
                                    return "" # Hata durumunda atla
                                
                                # İkon ve Renk Seçimi
                                bg_color = "#FFFFFF"
                                font_color = "#000000"
                                border_color = "#000000"
                                icon = ""
                                
                                if l_tip == 'Kat':
                                    bg_color = "#EBF5FB" # Açık Mavi
                                    border_color = "#2E86C1"
                                    icon = "🏢"
                                elif l_tip == 'Bölüm':
                                    bg_color = "#FEF9E7" # Açık Sarı
                                    border_color = "#F1C40F"
                                    icon = "🏭"
                                elif l_tip == 'Hat':
                                    bg_color = "#EAFAF1" # Açık Yeşil
                                    border_color = "#2ECC71"
                                    icon = "🛤️"
                                elif l_tip == 'Ekipman':
                                    bg_color = "#BDC3C7" # Koyu Gri (Görünür olması için)
                                    border_color = "#7F8C8D"
                                    icon = "⚙️"
                                
                                # Proses Bilgisi Var mı?
                                proses_txt = ""
                                if not proses_map.empty:
                                    p_list = proses_map[proses_map['lokasyon_id'] == loc_id]
                                    for _, p in p_list.iterrows():
                                        if pd.notna(p['proses_adi']):
                                            p_icon = p.get('ikon', '🔧')
                                            proses_txt += f"\\n[{p_icon} {p['proses_adi']}]"
                                
                                # Bu lokasyonun çocukları var mı?
                                children = tree.get(loc_id, [])
                                
                                output_dot = ""
                                
                                if children: # Eğer alt birimleri varsa, bu bir KÜME (Cluster) olur
                                    cluster_id = f"cluster_{loc_id}"
                                    # Graphviz label'ı HTML-like yapısız, düz string kullanıyoruz
                                    output_dot += f'\n  subgraph {cluster_id} {{\n'
                                    output_dot += f'    label="{icon} {l_ad}";\n'
                                    output_dot += f'    style="filled,rounded";\n'
                                    output_dot += f'    color="{border_color}";\n' # Çerçeve Rengi
                                    output_dot += f'    fillcolor="{bg_color}";\n' # Arka Plan Rengi
                                    output_dot += '    fontsize=11;\n'
                                    
                                    # Çocukları çiz
                                    for child_id in children:
                                        output_dot += draw_location_recursive_dot(child_id)
                                        
                                    output_dot += '  }\n'
                                    
                                else: # Eğer alt birimi yoksa, bu bir DÜĞÜM (Node) olur
                                    node_id = f"node_{loc_id}"
                                    label = f"{icon} {l_ad}\\n({l_tip}){proses_txt}"
                                    
                                    # Eğer ekipmansa şekli farklı olsun
                                    shape = "component" if l_tip == 'Ekipman' else "box"
                                    
                                    output_dot += f'    {node_id} [label="{label}", shape={shape}, fillcolor="{bg_color}", color="{border_color}", fontcolor="{font_color}"];\n'
                                
                                return output_dot

                            # Ana Çizim Döngüsü (Köklerden Başla)
                            if not roots:
                                st.warning("⚠️ Veri hatası: Kök lokasyon (Kat) bulunamadı. Lütfen lokasyon yapılandırmanızı kontrol edin.")
                            else:
                                for root_id in roots:
                                    dot += draw_location_recursive_dot(root_id)
                            
                            # ---------------------------------------------------------
                            # BAĞLANTILAR (AKIŞ)
                            # ---------------------------------------------------------
                            # Fiziksel hiyerarşiyi (Cluster) yukarıda belirledik.
                            # Şimdi mantıksal akışları (Hat -> Ekipman gibi) edge olarak ekleyebiliriz.
                            # Ancak cluster yapısında edge çizmek zordur (compound=true gerekir).
                            # Basitlik adına şu an sadece kutu içi kutu yapısını kullanıyoruz.
                            
                            dot += '}'
                            
                            # Çizim
                            st.graphviz_chart(dot, use_container_width=True)
                            
                            st.divider()
                            st.caption("Not: PDF çıktısı almak için tarayıcınızın yazdırma özelliğini kullanabilirsiniz.")

                    else:
                        st.warning("Henüz lokasyon tanımlanmamış. Ayarlar > Lokasyonlar menüsünden ekleyin.")
                        
                except Exception as e:
                    st.error(f"Harita oluşturulurken hata: {e}")

            # 6. PERSONEL ORGANİZASYON ŞEMASI (KURUMSAL GÖRÜNÜM - YENİ VERİ MODELİ)
            elif rapor_tipi == "👥 Personel Organizasyon Şeması":
                st.info("📊 Kurumsal organizasyon şeması - Personel hiyerarşisi (Yönetici-Çalışan İlişkisi)")
                
                # ═══════════════════════════════════════════════════════════
                # RECURSIVE HELPER FUNCTIONS (Dinamik Departman Ağacı)
                # ═══════════════════════════════════════════════════════════
                
                def get_all_departments():
                    """Tüm departmanları al"""
                    return pd.read_sql("""
                        SELECT id, bolum_adi, ana_departman_id, sira_no
                        FROM ayarlar_bolumler 
                        WHERE aktif = TRUE
                        ORDER BY sira_no
                    """, engine)
                
                def get_sub_departments(parent_id, all_depts):
                    """Belirli bir departmanın alt departmanlarını al"""
                    return all_depts[all_depts['ana_departman_id'] == parent_id].copy()
                
                def get_dept_staff(dept_id, pers_df):
                    """Belirli bir departmandaki personeli al"""
                    return pers_df[
                        (pers_df['departman_id'] == dept_id) & 
                        (pers_df['pozisyon_seviye'] >= 2)
                    ].copy()
                
                def count_total_staff_recursive(dept_id, all_depts, pers_df):
                    """Bir departman ve tüm alt departmanlarındaki toplam personel sayısı (recursive)"""
                    # Bu departmandaki personel
                    count = len(get_dept_staff(dept_id, pers_df))
                    
                    # Alt departmanlardaki personel (recursive)
                    sub_depts = get_sub_departments(dept_id, all_depts)
                    for _, sub in sub_depts.iterrows():
                        count += count_total_staff_recursive(sub['id'], all_depts, pers_df)
                    
                    return count
                
                def display_staff_by_level(staff_df, show_cards=True):
                    """Personeli seviyeye göre göster"""
                    if staff_df.empty:
                        return
                    
                    staff_df = staff_df.sort_values('pozisyon_seviye')
                    
                    # Yöneticiler (Seviye 2-4)
                    for seviye in [2, 3, 4]:
                        seviye_staff = staff_df[staff_df['pozisyon_seviye'] == seviye]
                        if not seviye_staff.empty:
                            seviye_label = f"{get_position_icon(seviye)} {get_position_name(seviye)}"
                            st.markdown(f"*{seviye_label}*")
                            
                            if show_cards:
                                cols = st.columns(min(len(seviye_staff), 3))
                                for idx, (_, person) in enumerate(seviye_staff.iterrows()):
                                    with cols[idx % 3]:
                                        gorev_text = person['gorev'] if pd.notna(person['gorev']) else person['rol']
                                        color = get_position_color(seviye)
                                        st.markdown(f"""
                                        <div style="
                                            background: {color};
                                            padding: 10px;
                                            border-radius: 6px;
                                            color: {'white' if seviye <= 3 else '#1A5276'};
                                            margin-bottom: 6px;
                                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                        ">
                                            <h6 style="margin:0; color:{'white' if seviye <= 3 else '#1A5276'};">👤 {person['ad_soyad']}</h6>
                                            <p style="margin:3px 0 0 0; font-size:11px; opacity:0.9;">{gorev_text}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                    
                    # Personel (Seviye 5-6)
                    personel_staff = staff_df[staff_df['pozisyon_seviye'] >= 5]
                    if not personel_staff.empty:
                        st.markdown(f"*{get_position_icon(5)} Personel* ({len(personel_staff)} kişi)")
                        cols = st.columns(3)
                        for idx, (_, person) in enumerate(personel_staff.iterrows()):
                            with cols[idx % 3]:
                                gorev = person['gorev'] if pd.notna(person['gorev']) else person['rol']
                                icon = "📝" if person['pozisyon_seviye'] == 6 else "👤"
                                st.markdown(f"• {icon} {person['ad_soyad']} *({gorev})*")
                
                def display_department_recursive(dept_id, dept_name, all_depts, pers_df, level=0, is_expanded=True):
                    """Departmanı ve tüm alt departmanlarını recursive olarak göster"""
                    # Bu departmandaki personel
                    dept_staff = get_dept_staff(dept_id, pers_df)
                    
                    # Alt departmanlar
                    sub_depts = get_sub_departments(dept_id, all_depts)
                    
                    # Toplam personel sayısı (bu departman + tüm alt departmanlar)
                    total_count = count_total_staff_recursive(dept_id, all_depts, pers_df)
                    
                    if total_count > 0:
                        # Departman başlığı
                        indent = "  " * level
                        icon = "🏢" if level == 0 else "📍"
                        
                        with st.expander(f"{icon} **{dept_name}** ({total_count} toplam personel)", expanded=is_expanded):
                            # Bu departmandaki personeli göster
                            if not dept_staff.empty:
                                if level > 0:
                                    st.markdown(f"**{dept_name} - Merkez** ({len(dept_staff)} kişi)")
                                display_staff_by_level(dept_staff)
                                
                                if not sub_depts.empty:
                                    st.markdown("---")
                            
                            # Alt departmanları recursive olarak göster
                            for _, sub_dept in sub_depts.iterrows():
                                sub_staff = get_dept_staff(sub_dept['id'], pers_df)
                                sub_sub_depts = get_sub_departments(sub_dept['id'], all_depts)
                                sub_total = count_total_staff_recursive(sub_dept['id'], all_depts, pers_df)
                                
                                if sub_total > 0:
                                    manager_count = len(sub_staff[sub_staff['pozisyon_seviye'] <= 4])
                                    staff_count = len(sub_staff[sub_staff['pozisyon_seviye'] > 4])
                                    
                                    st.markdown(f"**📍 {sub_dept['bolum_adi']}** ({manager_count} yönetici, {staff_count} personel)")
                                    display_staff_by_level(sub_staff)
                                    
                                    # Eğer alt departmanın da alt departmanları varsa, onları da göster (recursive)
                                    if not sub_sub_depts.empty:
                                        st.markdown(f"*Alt Birimler:*")
                                        for _, sub_sub in sub_sub_depts.iterrows():
                                            display_department_recursive(
                                                sub_sub['id'], 
                                                sub_sub['bolum_adi'], 
                                                all_depts, 
                                                pers_df, 
                                                level=level+2,
                                                is_expanded=False
                                            )
                                    
                                    st.markdown("")  # Boşluk
                
                def generate_dept_html_recursive(dept_id, dept_name, all_depts, pers_df, level=0):
                    """Liste görünümü için recursive HTML oluşturur"""
                    html = ""
                    
                    # Bu departmandaki personel
                    dept_staff = get_dept_staff(dept_id, pers_df)
                    
                    # Alt departmanlar
                    sub_depts = get_sub_departments(dept_id, all_depts)
                    
                    # Toplam personel sayısı (recursive)
                    total_count = count_total_staff_recursive(dept_id, all_depts, pers_df)
                    
                    if total_count > 0:
                        # Girinti hesapla & Başlık
                        if level == 0:
                           html += f'<div class="level-0">🏢 {dept_name.upper()} ({total_count} kişi)</div>'
                        else:
                           indent_px = 20 + ((level-1)*20)
                           html += f'<div class="dept-header" style="margin-left: {indent_px}px;">📍 {dept_name} ({total_count} kişi)</div>'
                        
                        # Bu departmandaki personeli ekle
                        if not dept_staff.empty:
                            staff_sorted = dept_staff.sort_values('pozisyon_seviye')
                            
                            # Yöneticiler (Seviye 2-4)
                            for seviye in [2, 3, 4]:
                                seviye_staff = staff_sorted[staff_sorted['pozisyon_seviye'] == seviye]
                                if not seviye_staff.empty:
                                    seviye_name = get_position_name(seviye)
                                    # Yönetici listesi
                                    for _, person in seviye_staff.iterrows():
                                        gorev = person['gorev'] if pd.notna(person['gorev']) else person['rol']
                                        # Yönetici stili (biraz daha içeride)
                                        margin_left = 60 + (level * 20)
                                        # Seviye ikonunu ekle
                                        icon = get_position_icon(seviye)
                                        html += f'<div class="level-3" style="margin-left: {margin_left}px;">{icon} <b>{person["ad_soyad"]}</b> ({seviye_name}) - {gorev}</div>'
                            
                            # Personel (Seviye 5-6)
                            personel_staff = staff_sorted[staff_sorted['pozisyon_seviye'] >= 5]
                            if not personel_staff.empty:
                                margin_left_header = 40 + (level * 20)
                                # Personel başlığı göstermek yerine direkt listeleyelim veya sade başlık
                                # html += f'<div class="level-2" style="margin-left: {margin_left_header}px; font-size:12px;">👥 Personel ({len(personel_staff)})</div>'
                                
                                margin_left_item = 80 + (level * 20)
                                for _, person in personel_staff.iterrows():
                                    gorev = person['gorev'] if pd.notna(person['gorev']) else person['rol']
                                    icon = "📝" if person['pozisyon_seviye'] == 6 else "•"
                                    html += f'<div class="level-4" style="margin-left: {margin_left_item}px;">{icon} {person["ad_soyad"]} - {gorev}</div>'
                        
                        # Alt departmanları recursive işle
                        for _, sub in sub_depts.iterrows():
                            html += generate_dept_html_recursive(sub['id'], sub['bolum_adi'], all_depts, pers_df, level + 1)
                            
                    return html
                

                try:
                    # YENİ: v_organizasyon_semasi view'ından veri çek
                    pers_df = get_personnel_hierarchy()
                    
                    # Debug bilgisi
                    if pers_df.empty:
                        st.warning("⚠️ Personel verisi bulunamadı.")
                        st.info("💡 Önce Ayarlar > Kullanıcı Yönetimi'nden personel ekleyin ve organizasyonel bilgilerini (Departman, Yönetici, Pozisyon Seviyesi) doldurun.")
                    elif 'pozisyon_seviye' not in pers_df.columns:
                        st.error("⚠️ Personel verisinde 'pozisyon_seviye' kolonu bulunamadı.")
                        st.info("💡 Eğer migration script'i henüz çalıştırmadıysanız, lütfen önce sql/supabase_personel_org_restructure.sql dosyasını Supabase SQL Editor'de çalıştırın.")
                        with st.expander("Mevcut Kolonlar"):
                            st.write(list(pers_df.columns))
                    
                    if not pers_df.empty and 'pozisyon_seviye' in pers_df.columns:
                        
                        # ═══════════════════════════════════════════════════════════
                        # İNTERAKTİF GÖRÜNÜM (Streamlit Columns)
                        # ═══════════════════════════════════════════════════════════
                        if gorunum_tipi == "🖥️ İnteraktif Görünüm (Ekran)":
                            st.markdown("### 👔 Kurumsal Organizasyon Yapısı")
                            
                            # Üst yönetimi göster (Seviye 0-1: Yönetim Kurulu, Genel Müdür)
                            ust_yonetim = pers_df[pers_df['pozisyon_seviye'] <= 1].copy()
                            if not ust_yonetim.empty:
                                st.markdown("#### 🏛️ Üst Yönetim")
                                cols = st.columns(min(len(ust_yonetim), 3))
                                for idx, (_, yonetici) in enumerate(ust_yonetim.iterrows()):
                                    with cols[idx]:
                                        gorev_text = yonetici['gorev'] if pd.notna(yonetici['gorev']) else yonetici['rol']
                                        st.markdown(f"""
                                        <div style="
                                            background: linear-gradient(135deg, #1A5276 0%, #2874A6 100%);
                                            padding: 20px;
                                            border-radius: 12px;
                                            color: white;
                                            margin-bottom: 15px;
                                            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                                            text-align: center;
                                        ">
                                            <h3 style="margin:0; color:white;">{get_position_icon(int(yonetici['pozisyon_seviye']))} {yonetici['ad_soyad']}</h3>
                                            <p style="margin:10px 0 0 0; font-size:16px; opacity:0.95;">{gorev_text}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                st.divider()
                            
                            # Departman bazlı organizasyon (Recursive - Tamamen Dinamik)
                            st.markdown("#### 🏢 Departman Organizasyonu")
                            
                            # Tüm departmanları al
                            all_depts = get_all_departments()
                            
                            # Sadece üst seviye departmanları bul
                            # 1. Ana departmanı OLMAYANLAR (NULL)
                            # 2. Veya Ana departmanı YÖNETİM (1) OLANLAR
                            top_level_depts = all_depts[
                                (all_depts['ana_departman_id'].isna()) | 
                                (all_depts['ana_departman_id'] == 1)
                            ]
                            
                            for _, dept in top_level_depts.iterrows():
                                dept_id = dept['id']
                                dept_name = dept['bolum_adi']
                                if dept_id != 1: # YÖNETİM hariç (üstte zaten gösterdik)
                                    display_department_recursive(dept_id, dept_name, all_depts, pers_df)
                            
                            # Departmanı olmayan personel varsa göster
                            no_dept_staff = pers_df[pers_df['departman_id'].isna() & (pers_df['pozisyon_seviye'] >= 2)].copy()
                            if not no_dept_staff.empty:
                                st.divider()
                                with st.expander(f"❓ **Departman Atanmamış** ({len(no_dept_staff)} kişi)", expanded=False):
                                    st.warning("Bu personelin departman ataması yapılmalı!")
                                    for _, person in no_dept_staff.iterrows():
                                        gorev = person['gorev'] if pd.notna(person['gorev']) else person['rol']
                                        st.markdown(f"• {person['ad_soyad']} - {gorev} (Seviye {int(person['pozisyon_seviye'])})")
                        
                        # ═══════════════════════════════════════════════════════════
                        # PDF ÇIKTISI (Graphviz - Mevcut Kod)
                        # ═══════════════════════════════════════════════════════════
                        elif gorunum_tipi == "📄 PDF Çıktısı (Yazdırma)":
                            # PDF için spinner göster (donma hissi önlenir)
                            with st.spinner("🔄 Organizasyon şeması oluşturuluyor... Lütfen bekleyiniz."):
                                st.info("ℹ️ Büyük organizasyonlarda bu işlem 10-15 saniye sürebilir.")
                            
                            # Graphviz DOT Kodu - Gerçek Hiyerarşik Organizasyon Şeması
                            dot = 'digraph OrgChart {\n'
                            dot += '  rankdir=TB;\n'  # Yukarıdan Aşağıya
                            dot += '  splines=ortho;\n'  # Köşeli çizgiler
                            dot += '  nodesep=0.25;\n'   # Düğümler arası mesafe (iyice azaltıldı)
                            dot += '  ranksep=0.5;\n'    # Seviyeler arası mesafe (azaltıldı)
                            dot += '  ratio="fill";\n'   # Sayfayı doldur (gerekirse scale et)
                            dot += '  size="11.7,8.3!";\n' # A4 Yatay (Landscape) Boyutu - ÜNLEM ZORLA SIĞDIR DEMEK
                            dot += '  margin=0.1;\n'     # Kenar boşluğu minimize edildi
                            
                            # Genel Stil - Fontları küçült
                            dot += '  node [shape=box, style="filled,rounded", fontname="Arial", fontsize=9, height=0.4];\n'
                            dot += '  edge [color="#34495E", penwidth=1.5, arrowhead=vee, arrowsize=0.7];\n'
                            
                            # Renk Paleti (Pozisyon Seviyesine Göre) - constants'tan al
                            seviye_renkler = {
                                level: get_position_color(level) 
                                for level in POSITION_LEVELS.keys()
                            }
                            
                            # Departman renkleri (Cluster arka planı için)
                            dept_colors = {}
                            dept_list = pers_df['departman'].dropna().unique()
                            for idx, dept in enumerate(dept_list):
                                dept_colors[dept] = f'/pastel19/{(idx % 9) + 1}'  # Pastel renkler
                            
                            # Departman bazlı cluster'lar oluştur
                            dept_clusters = {}
                            for dept in dept_list:
                                dept_pers = pers_df[pers_df['departman'] == dept]
                                if not dept_pers.empty:
                                    dept_clusters[dept] = dept_pers
                            
                            # Her departman için cluster oluştur
                            for dept_name, dept_pers in dept_clusters.items():
                                cluster_id = f"cluster_{dept_name.replace(' ', '_').replace('>', '_')}"
                                dot += f'\n  subgraph {cluster_id} {{\n'
                                dot += f'    label="{dept_name}";\n'
                                dot += '    style=filled;\n'
                                dot += f'    color="{dept_colors.get(dept_name, "lightgrey")}";\n'
                                dot += '    fontsize=11;\n'
                                dot += '    fontname="Arial Bold";\n'
                                
                                # Bu departmandaki personeli ekle
                                for _, p in dept_pers.iterrows():
                                    p_id = int(p['id'])
                                    p_ad = str(p['ad_soyad']).replace('"', "'")
                                    p_gorev = str(p['gorev']).replace('"', "'") if pd.notna(p['gorev']) else str(p['rol'])
                                    p_seviye = int(p['pozisyon_seviye']) if pd.notna(p['pozisyon_seviye']) else 5
                                    
                                    # Renk seç
                                    renk = seviye_renkler.get(p_seviye, '#D4E6F1')
                                    font_renk = 'white' if p_seviye < 3 else '#1A5276'
                                    
                                    # Node label
                                    label = f"{p_ad}\\n{p_gorev}"
                                    
                                    # Node oluştur
                                    node_id = f"pers_{p_id}"
                                    dot += f'    {node_id} [label="{label}", fillcolor="{renk}", fontcolor="{font_renk}", penwidth=0];\n'
                                
                                dot += '  }\n'
                            
                            # Departman dışındaki personeli 'Tanımsız' kümesine ekle (ZORUNLU - PDF Hatalarını Önler)
                            no_dept_pers = pers_df[pers_df['departman'].isna() | (pers_df['departman'] == 'Tanımsız')]
                            if not no_dept_pers.empty:
                                dot += '\n  subgraph cluster_nan {\n'
                                dot += '    label="Departman Atanmamış";\n'
                                dot += '    style=dotted;\n'
                                dot += '    color=red;\n'
                                
                                for _, p in no_dept_pers.iterrows():
                                    p_id = int(p['id'])
                                    p_ad = str(p['ad_soyad']).replace('"', "'")
                                    p_gorev = str(p['gorev']).replace('"', "'") if pd.notna(p['gorev']) else str(p['rol'])
                                    p_seviye = int(p['pozisyon_seviye']) if pd.notna(p['pozisyon_seviye']) else 5
                                    
                                    renk = seviye_renkler.get(p_seviye, '#D4E6F1')
                                    font_renk = 'white' if p_seviye < 3 else '#1A5276'
                                    label = f"{p_ad}\\n{p_gorev}"
                                    node_id = f"pers_{p_id}"
                                    dot += f'    {node_id} [label="{label}", fillcolor="{renk}", fontcolor="{font_renk}", penwidth=0];\n'
                                
                                dot += '  }\n'
                            
                            # Yönetici-Çalışan İlişkilerini Edge olarak ekle (yonetici_id)
                            dot += '\n  // Hiyerarşik İlişkiler (Yönetici -> Çalışan)\n'
                            for _, p in pers_df.iterrows():
                                if pd.notna(p['yonetici_id']):
                                    yonetici_id = int(p['yonetici_id'])
                                    calisan_id = int(p['id'])
                                    dot += f'  pers_{yonetici_id} -> pers_{calisan_id};\n'
                            
                            dot += '}'
                            
                            # Çiz
                            try:
                                st.graphviz_chart(dot, use_container_width=True)
                                
                                # PDF İndirme
                                try:
                                    source = graphviz.Source(dot)
                                    pdf_data = source.pipe(format='pdf')
                                    st.download_button(
                                        label="📄 Organizasyon Şemasını PDF Olarak İndir",
                                        data=pdf_data,
                                        file_name="personel_organizasyon_semasi.pdf",
                                        mime="application/pdf",
                                        key="download_org_chart_personnel"
                                    )
                                except graphviz.backend.ExecutableNotFound:
                                    st.warning("⚠️ PDF oluşturulamadı: Sunucuda 'Graphviz' yazılımı yüklü değil.")
                                    st.info("Tarayıcınızın 'Yazdır > PDF Olarak Kaydet' özelliğini kullanabilirsiniz.")
                                except Exception as e:
                                    st.error(f"PDF hatası: {e}")
                                    
                            except Exception as e:
                                st.error(f"Görselleştirme hatası: {e}")
                                with st.expander("DOT Kodu (Debug)"):
                                    st.code(dot)
                            
                            # Renk Açıklaması (sadece PDF görünümünde)
                            st.divider()
                            col1, col2 = st.columns(2)
                            with col1:
                                st.caption("**Renk Açıklaması (Pozisyon Seviyesi):**")
                                st.markdown("🔵 Koyu Mavi = Üst Yönetim (Seviye 0-2)")
                                st.markdown("🔷 Açık Mavi = Orta Kademe (Seviye 3-4)")
                                st.markdown("⚪ Beyaz/Gri = Personel (Seviye 5-6)")
                            with col2:
                                st.caption("**Oklar:** Yönetici → Çalışan ilişkisini gösterir")
                                st.caption("**Kutular:** Departman gruplarını gösterir")
                            
                            # İstatistikler
                            st.divider()
                            st.subheader("📊 Organizasyon İstatistikleri")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Toplam Personel", len(pers_df))
                            with col2:
                                ust_yonetim = len(pers_df[pers_df['pozisyon_seviye'] <= 2])
                                st.metric("Üst Yönetim", ust_yonetim)
                            with col3:
                                orta_kademe = len(pers_df[(pers_df['pozisyon_seviye'] >= 3) & (pers_df['pozisyon_seviye'] <= 4)])
                                st.metric("Orta Kademe", orta_kademe)
                            with col4:
                                personel = len(pers_df[pers_df['pozisyon_seviye'] >= 5])
                                st.metric("Personel", personel)
                        
                        # ═══════════════════════════════════════════════════════════
                        # LİSTE FORMATI (A4 Yatay - Basit Hiyerarşik Liste)
                        # ═══════════════════════════════════════════════════════════
                        elif gorunum_tipi == "📋 Liste Formatı (A4 Yatay)":
                            st.markdown("### 📋 Kurumsal Organizasyon Listesi")
                            st.caption("A4 Yatay formatta yazdırma için optimize edilmiştir")
                            
                            # Hiyerarşik liste oluştur
                            liste_html = """
                            <style>
                                @media print {
                                    @page { size: landscape; margin: 1cm; }
                                    body { font-size: 10pt; }
                                }
                                .org-list { font-family: Arial, sans-serif; line-height: 1.6; }
                                .level-0 { font-size: 18px; font-weight: bold; color: #1A5276; margin-top: 20px; }
                                .level-1 { font-size: 16px; font-weight: bold; color: #2874A6; margin-top: 15px; margin-left: 20px; }
                                .level-2 { font-size: 14px; font-weight: bold; color: #3498DB; margin-top: 10px; margin-left: 40px; }
                                .level-3 { font-size: 13px; font-weight: 600; color: #5DADE2; margin-top: 8px; margin-left: 60px; }
                                .level-4 { font-size: 12px; color: #85C1E9; margin-left: 80px; }
                                .level-5 { font-size: 11px; color: #34495E; margin-left: 100px; }
                                .dept-header { font-weight: bold; color: #2C3E50; margin-top: 15px; margin-left: 40px; border-bottom: 1px solid #BDC3C7; padding-bottom: 5px; }
                            </style>
                            <div class="org-list">
                            """
                            
                            # Üst Yönetim (Seviye 0-1)
                            ust_yonetim = pers_df[pers_df['pozisyon_seviye'] <= 1].sort_values('pozisyon_seviye')
                            if not ust_yonetim.empty:
                                liste_html += '<div class="level-0">🏛️ ÜST YÖNETİM</div>'
                                for _, person in ust_yonetim.iterrows():
                                    gorev = person['gorev'] if pd.notna(person['gorev']) else person['rol']
                                    liste_html += f'<div class="level-1">• {person["ad_soyad"]} - {gorev}</div>'
                            
                            # RECURSIVE HTML GENERATION
                            all_depts = get_all_departments()
                            # Üst seviye departmanlar (Sahipsiz veya Yönetim'e bağlı)
                            top_level_depts = all_depts[
                                (all_depts['ana_departman_id'].isna()) | 
                                (all_depts['ana_departman_id'] == 1)
                            ]
                            
                            for _, dept in top_level_depts.iterrows():
                                if dept['id'] != 1: # YÖNETİM hariç
                                    liste_html += generate_dept_html_recursive(dept['id'], dept['bolum_adi'], all_depts, pers_df)
                            
                            liste_html += "</div>"
                            
                            # HTML'i göster
                            st.markdown(liste_html, unsafe_allow_html=True)
                            
                            # ═══════════════════════════════════════════════════════════
                            # YAZDIRILABİLİR HTML DOSYASI OLUŞTURMA
                            # ═══════════════════════════════════════════════════════════
                            
                            # Tam HTML şablonu (Head, Body, Auto-Print JS)
                            full_html = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <title>Organizasyon Listesi</title>
                                <style>
                                    @page {{ size: A4 landscape; margin: 1cm; }}
                                    body {{ font-family: Arial, sans-serif; font-size: 10pt; line-height: 1.4; }}
                                    .org-list {{ width: 100%; }}
                                    .level-0 {{ font-size: 16px; font-weight: bold; color: #1A5276; margin-top: 15px; border-bottom: 2px solid #1A5276; padding-bottom: 5px; page-break-after: avoid; }}
                                    .level-1 {{ font-size: 14px; font-weight: bold; color: #2874A6; margin-top: 10px; margin-left: 20px; }}
                                    .level-2 {{ font-size: 12px; font-weight: bold; color: #3498DB; margin-top: 5px; margin-left: 40px; }}
                                    .level-3 {{ font-size: 11px; font-weight: 600; color: #5DADE2; margin-top: 2px; margin-left: 60px; }}
                                    .level-4 {{ font-size: 10px; color: #34495E; margin-left: 80px; }}
                                    .dept-header {{ font-weight: bold; color: #2C3E50; margin-top: 10px; margin-left: 40px; border-bottom: 1px dotted #ccc; width: 80%; page-break-after: avoid; }}
                                    /* Sadece yazdırma sırasında görünen başlık */
                                    @media print {{
                                        .no-print {{ display: none; }}
                                    }}
                                </style>
                            </head>
                            <body>
                                <h2 style="text-align:center; color:#2C3E50;">EKLERİSTAN GIDA - ORGANİZASYON ŞEMASI LİSTESİ</h2>
                                <p style="text-align:center; font-size:10px; color:#777;">Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                                <hr>
                                {liste_html}
                                <script>
                                    // Sayfa yüklendiğinde otomatik yazdırma penceresini aç
                                    window.onload = function() {{ window.print(); }}
                                </script>
                            </body>
                            </html>
                            """
                            
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.download_button(
                                    label="🖨️ Yazdır / PDF Olarak Kaydet",
                                    data=full_html,
                                    file_name="organizasyon_listesi.html",
                                    mime="text/html",
                                    help="Tıkladığınızda açılan dosyayı tarayıcınızdan yazdırabilirsiniz (Otomatik A4 Yatay ayarlı)"
                                )
                            with col2:
                                st.info("ℹ️ İndirilen dosyayı açtığınızda otomatik olarak yazdırma ekranı gelir. Hedef olarak **'PDF Olarak Kaydet'** seçebilirsiniz.")
                        
                except Exception as e:
                    st.error(f"Organizasyon şeması oluşturulurken hata: {e}")
                    st.info("💡 Eğer migration script'i henüz çalıştırmadıysanız, lütfen önce `sql/supabase_personel_org_restructure.sql` dosyasını Supabase SQL Editor'de çalıştırın.")


    # >>> MODÜL: AYARLAR <<<   
    elif menu == "⚙️ Ayarlar":
        # Yetki kontrolü - Ayarlar sadece Admin'e açık
        if not kullanici_yetkisi_var_mi(menu, "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır.")
            st.info("💡 Ayarlar modülüne erişim için Admin yetkisi gereklidir.")
            st.stop()
        
        st.title("⚙️ Sistem Ayarları ve Personel Yönetimi")
        
        
        # Sekmeleri tanımlıyoruz - Lokasyon ve Proses yönetimi eklendi
        tab1, tab2, tab3, tab_rol, tab_yetki, tab_bolumler, tab_lokasyon, tab_proses, tab_tanimlar, tab_gmp_soru = st.tabs([
            "👥 Personel", 
            "🔐 Kullanıcılar", 
            "📦 Ürünler",
            "🎭 Roller",
            "🔑 Yetkiler",
            "🏭 Bölümler",
            "📍 Lokasyonlar",
            "🔧 Prosesler",
            "🧹 Temizlik & Bölümler",
            "🛡️ GMP Sorular"
        ])
        



        with tab1:
            st.subheader("👷 Fabrika Personel Listesi Yönetimi")
            
            # Alt sekmeler: Form ve Tablo
            subtab_form, subtab_table = st.tabs(["📝 Personel Ekle/Düzenle", "📋 Tüm Personel Listesi"])
            
            with subtab_form:
                st.caption("Yeni personel ekleyin veya mevcut personeli düzenleyin")
                
                # Dropdown seçeneklerini hazırla
                try:
                    dept_df = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler WHERE aktif = TRUE ORDER BY sira_no", engine)
                    dept_options = {0: "- Seçiniz -"}
                    for _, row in dept_df.iterrows():
                        dept_options[row['id']] = row['bolum_adi']
                except:
                    dept_options = {0: "- Seçiniz -"}
                
                try:
                    yonetici_df = pd.read_sql("SELECT id, ad_soyad FROM personel WHERE ad_soyad IS NOT NULL ORDER BY ad_soyad", engine)
                    yonetici_options = {0: "- Yok -"}
                    for _, row in yonetici_df.iterrows():
                        yonetici_options[row['id']] = row['ad_soyad']
                except:
                    yonetici_options = {0: "- Yok -"}
                
                seviye_options = {
                    0: "0 - Yönetim Kurulu",
                    1: "1 - Genel Müdür / CEO",
                    2: "2 - Direktör",
                    3: "3 - Müdür",
                    4: "4 - Şef / Sorumlu / Koordinatör",
                    5: "5 - Personel (Varsayılan)",
                    6: "6 - Stajyer / Çırak"
                }
                
                # Mod seçimi: Yeni Ekle veya Mevcut Düzenle
                mod = st.radio(
                    "İşlem Türü",
                    ["➕ Yeni Personel Ekle", "✏️ Mevcut Personeli Düzenle"],
                    horizontal=True
                )
                
                # Mevcut personeli düzenle modunda personel seçimi
                selected_pers_id = None
                if mod == "✏️ Mevcut Personeli Düzenle":
                    try:
                        pers_list_df = pd.read_sql("SELECT id, ad_soyad FROM personel WHERE ad_soyad IS NOT NULL ORDER BY ad_soyad", engine)
                        pers_select_options = {row['id']: row['ad_soyad'] for _, row in pers_list_df.iterrows()}
                        selected_pers_id = st.selectbox(
                            "Düzenlenecek Personeli Seçin",
                            options=list(pers_select_options.keys()),
                            format_func=lambda x: pers_select_options[x]
                        )
                        
                        # Seçilen personelin mevcut verilerini çek
                        if selected_pers_id:
                            current_pers = pd.read_sql(f"SELECT * FROM personel WHERE id = {selected_pers_id}", engine).iloc[0]
                    except:
                        st.warning("Personel listesi yüklenemedi")
                        current_pers = None
                else:
                    current_pers = None
                
                # Form
                with st.form("personel_form"):
                    col1, col2 = st.columns(2)
                    
                    # Temel Bilgiler
                    ad_soyad = col1.text_input(
                        "👤 Ad Soyad *",
                        value=current_pers['ad_soyad'] if current_pers is not None and pd.notna(current_pers.get('ad_soyad')) else ""
                    )
                    
                    gorev = col2.text_input(
                        "💼 Görev",
                        value=current_pers['gorev'] if current_pers is not None and pd.notna(current_pers.get('gorev')) else ""
                    )
                    
                    # Organizasyonel Bilgiler
                    st.divider()
                    st.caption("🏢 Organizasyonel Bilgiler")
                    
                    departman_id = col1.selectbox(
                        "🏭 Departman",
                        options=list(dept_options.keys()),
                        format_func=lambda x: dept_options[x],
                        index=list(dept_options.keys()).index(current_pers['departman_id']) if current_pers is not None and pd.notna(current_pers.get('departman_id')) and current_pers['departman_id'] in dept_options else 0
                    )
                    
                    yonetici_id = col2.selectbox(
                        "👔 Doğrudan Yönetici",
                        options=list(yonetici_options.keys()),
                        format_func=lambda x: yonetici_options[x],
                        index=list(yonetici_options.keys()).index(current_pers['yonetici_id']) if current_pers is not None and pd.notna(current_pers.get('yonetici_id')) and current_pers['yonetici_id'] in yonetici_options else 0
                    )
                    
                    pozisyon_seviye = col1.selectbox(
                        "📊 Pozisyon Seviyesi",
                        options=list(seviye_options.keys()),
                        format_func=lambda x: seviye_options[x],
                        index=list(seviye_options.keys()).index(current_pers['pozisyon_seviye']) if current_pers is not None and pd.notna(current_pers.get('pozisyon_seviye')) and current_pers['pozisyon_seviye'] in seviye_options else 5
                    )
                    
                    # Çalışma Bilgileri
                    st.divider()
                    st.caption("📅 Çalışma Bilgileri")
                    
                    vardiya = col2.selectbox(
                        "Vardiya",
                        options=["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"],
                        index=["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"].index(current_pers['vardiya']) if current_pers is not None and pd.notna(current_pers.get('vardiya')) and current_pers['vardiya'] in ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"] else 0
                    )
                    
                    durum = col1.selectbox(
                        "Durum",
                        options=["AKTİF", "PASİF"],
                        index=["AKTİF", "PASİF"].index(current_pers['durum']) if current_pers is not None and pd.notna(current_pers.get('durum')) and current_pers['durum'] in ["AKTİF", "PASİF"] else 0
                    )
                    
                    # [YENİ] Pasife Alma / İşten Çıkış Bilgileri
                    st.caption("🔻 İşten Çıkış Bilgileri (Sadece Durum PASİF ise doldurun)")
                    c_out1, c_out2 = st.columns(2)
                    
                    # Çıkış tarihi logic
                    out_date_val = None
                    if current_pers is not None and pd.notna(current_pers.get('is_cikis_tarihi')):
                        try:
                            parsed_out = pd.to_datetime(current_pers['is_cikis_tarihi'])
                            if not pd.isna(parsed_out): out_date_val = parsed_out.date()
                        except: pass
                    
                    is_cikis_tarihi = c_out1.date_input("İşten Çıkış Tarihi", value=out_date_val)
                    ayrilma_sebebi = c_out2.text_input(
                        "Ayrılma Sebebi", 
                        value=current_pers['ayrilma_sebebi'] if current_pers is not None and pd.notna(current_pers.get('ayrilma_sebebi')) else "",
                        placeholder="Örn: İstifa, Emeklilik vb."
                    )
                    
                    # İşe giriş tarihi - NaT kontrolü ile
                    ise_giris_value = None
                    if current_pers is not None and pd.notna(current_pers.get('ise_giris_tarihi')):
                        try:
                            parsed_date = pd.to_datetime(current_pers['ise_giris_tarihi'])
                            # NaT kontrolü
                            if not pd.isna(parsed_date):
                                ise_giris_value = parsed_date.date()
                        except:
                            ise_giris_value = None
                    
                    ise_giris_tarihi = col2.date_input(
                        "İşe Giriş Tarihi",
                        value=ise_giris_value
                    )
                    
                    izin_gunu = col1.selectbox(
                        "İzin Günü",
                        options=["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar", "-"],
                        index=["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar", "-"].index(current_pers['izin_gunu']) if current_pers is not None and pd.notna(current_pers.get('izin_gunu')) and current_pers['izin_gunu'] in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar", "-"] else 7
                    )
                    
                    # Kaydet Butonu
                    submit = st.form_submit_button(
                        "💾 Kaydet" if mod == "➕ Yeni Personel Ekle" else "💾 Güncelle",
                        type="primary",
                        use_container_width=True
                    )
                    
                    if submit:
                        if not ad_soyad:
                            st.error("Ad Soyad zorunludur!")
                        else:
                            try:
                                with engine.connect() as conn:
                                    dept_val = None if departman_id == 0 else departman_id
                                    yonetici_val = None if yonetici_id == 0 else yonetici_id
                                    
                                    if mod == "✏️ Mevcut Personeli Düzenle" and selected_pers_id:
                                        # UPDATE
                                        sql = text("""
                                            UPDATE personel 
                                            SET ad_soyad = :ad, gorev = :gorev, departman_id = :dept, 
                                                yonetici_id = :yon, pozisyon_seviye = :poz, vardiya = :var,
                                                durum = :dur, ise_giris_tarihi = :igt, izin_gunu = :ig,
                                                is_cikis_tarihi = :ict, ayrilma_sebebi = :as
                                            WHERE id = :id
                                        """)
                                        conn.execute(sql, {
                                            "ad": ad_soyad, "gorev": gorev, "dept": dept_val,
                                            "yon": yonetici_val, "poz": pozisyon_seviye, "var": vardiya,
                                            "dur": durum, "igt": str(ise_giris_tarihi) if ise_giris_tarihi else None,
                                            "ig": izin_gunu, "id": selected_pers_id,
                                            "ict": str(is_cikis_tarihi) if durum == 'PASİF' and is_cikis_tarihi else None,
                                            "as": ayrilma_sebebi if durum == 'PASİF' else None
                                        })
                                        st.success(f"✅ {ad_soyad} güncellendi!")
                                    else:
                                        # INSERT
                                        sql = text("""
                                            INSERT INTO personel 
                                            (ad_soyad, gorev, departman_id, yonetici_id, pozisyon_seviye,
                                             vardiya, durum, ise_giris_tarihi, izin_gunu, is_cikis_tarihi, ayrilma_sebebi)
                                            VALUES (:ad, :gorev, :dept, :yon, :poz, :var, :dur, :igt, :ig, :ict, :as)
                                        """)
                                        conn.execute(sql, {
                                            "ad": ad_soyad, "gorev": gorev, "dept": dept_val,
                                            "yon": yonetici_val, "poz": pozisyon_seviye, "var": vardiya,
                                            "dur": durum, "igt": str(ise_giris_tarihi) if ise_giris_tarihi else None,
                                            "ig": izin_gunu,
                                            "ict": str(is_cikis_tarihi) if durum == 'PASİF' and is_cikis_tarihi else None,
                                            "as": ayrilma_sebebi if durum == 'PASİF' else None
                                        })
                                        st.success(f"✅ {ad_soyad} eklendi!")
                                    
                                    conn.commit()
                                    cached_veri_getir.clear()
                                    get_personnel_hierarchy.clear()
                                    time.sleep(1)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Hata: {e}")
            
            # >>> ALT SEKME 2: TABLO <<<
            with subtab_table:
                st.caption("Tüm personel listesini görüntüleyin ve toplu düzenleme yapın")
                try:
                    # Dinamik bölüm listesini hiyerarşik olarak al (Örn: Üretim > Sos Ekleme)
                    bolum_listesi = get_department_hierarchy()
                    if not bolum_listesi:
                        bolum_listesi = ["Üretim", "Paketleme", "Depo", "Ofis", "Kalite"]
                    
                    # Tüm tabloyu çek
                    pers_df = pd.read_sql("SELECT * FROM personel", engine)
                    
                    # ise_giris_tarihi sütununu string'e çevir (Streamlit'in date olarak algılamasını önle)
                    if 'ise_giris_tarihi' in pers_df.columns:
                        pers_df['ise_giris_tarihi'] = pers_df['ise_giris_tarihi'].astype(str).replace('None', '').replace('nan', '').replace('NaT', '')
                    
                    # Yeni alanlar için dropdown seçeneklerini hazırla
                    # Departman listesi (Foreign Key için ID bazlı)
                    try:
                        dept_df = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler WHERE aktif = TRUE ORDER BY sira_no", engine)
                        dept_id_to_name = {row['id']: row['bolum_adi'] for _, row in dept_df.iterrows()}
                        dept_name_list = list(dept_id_to_name.values())
                        dept_name_list.insert(0, "- Seçiniz -")
                    except:
                        dept_id_to_name = {}
                        dept_name_list = ["- Seçiniz -"]
                
                    # Yönetici listesi (Self-referencing FK için ID bazlı)
                    try:
                        yonetici_df = pd.read_sql("SELECT id, ad_soyad FROM personel WHERE ad_soyad IS NOT NULL ORDER BY ad_soyad", engine)
                        yonetici_id_to_name = {row['id']: row['ad_soyad'] for _, row in yonetici_df.iterrows()}
                        yonetici_name_list = list(yonetici_id_to_name.values())
                        yonetici_name_list.insert(0, "- Yok -")
                    except:
                        yonetici_id_to_name = {}
                        yonetici_name_list = ["- Yok -"]
                    
                    # Pozisyon seviyesi mapping
                    seviye_list = [
                        "0 - Yönetim Kurulu",
                        "1 - Genel Müdür / CEO",
                        "2 - Direktör",
                        "3 - Müdür",
                        "4 - Şef / Sorumlu / Koordinatör",
                        "5 - Personel (Varsayılan)",
                        "6 - Stajyer / Çırak"
                    ]
                    
                    # Yardımcı sütunlar ekle (ID -> İsim dönüşümü için)
                    # Departman ID -> İsim
                    pers_df['departman_adi'] = pers_df['departman_id'].map(dept_id_to_name)
                    pers_df['departman_adi'] = pers_df['departman_adi'].fillna("- Seçiniz -")
                    
                    # Yönetici ID -> İsim
                    pers_df['yonetici_adi'] = pers_df['yonetici_id'].map(yonetici_id_to_name)
                    pers_df['yonetici_adi'] = pers_df['yonetici_adi'].fillna("- Yok -")
                    
                    # Pozisyon Seviye -> Açıklama
                    pers_df['pozisyon_adi'] = pers_df['pozisyon_seviye'].apply(
                        lambda x: seviye_list[int(x)] if pd.notna(x) and 0 <= int(x) <= 6 else "5 - Personel (Varsayılan)"
                    )
                    
                    # Düzenlenebilir Editör
                    # Gizlenecek teknik sütunları config ile saklıyoruz (şifre, rol, kullanıcı adı admin panelinde yönetilsin)
                    edited_pers = st.data_editor(
                        pers_df,
                        num_rows="dynamic",
                        use_container_width=True,
                        key="editor_personel_main",
                        column_config={
                            "id": None,  # Gizle (auto-increment)
                            "kullanici_adi": None, # Gizle
                            "sifre": None,         # Gizle
                            "rol": None,           # Gizle
                            "departman_id": None,  # Gizle (ID yerine departman_adi gösteriyoruz)
                            "yonetici_id": None,   # Gizle (ID yerine yonetici_adi gösteriyoruz)
                            "pozisyon_seviye": None,  # Gizle (Sayı yerine pozisyon_adi gösteriyoruz)
                            "ad_soyad": st.column_config.TextColumn("👤 Adı Soyadı", required=True, width="medium"),
                            "departman_adi": st.column_config.SelectboxColumn(
                                "🏭 Departman",
                                options=dept_name_list,
                                help="Personelin çalıştığı departman",
                                width="medium"
                            ),
                            "yonetici_adi": st.column_config.SelectboxColumn(
                                "👔 Yönetici",
                                options=yonetici_name_list,
                                help="Doğrudan yönetici",
                                width="medium"
                            ),
                            "pozisyon_adi": st.column_config.SelectboxColumn(
                                "📊 Pozisyon",
                                options=seviye_list,
                                help="Organizasyon hiyerarşisindeki seviye",
                                width="medium"
                            ),
                            "gorev": st.column_config.TextColumn("💼 Görevi", width="medium"),
                            "bolum": None,  # Gizle - Artık departman_adi kullanıyoruz
                            "vardiya": st.column_config.SelectboxColumn("Vardiya", options=["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], width="small"),
                            "durum": st.column_config.SelectboxColumn("Durum", options=["AKTİF", "PASİF"], width="small"),
                            "ise_giris_tarihi": st.column_config.TextColumn("İşe Giriş", width="small", disabled=False),
                            "sorumlu_bolum": None,  # Gizle - Gereksiz (gorev alanı yeterli)
                            "izin_gunu": st.column_config.SelectboxColumn("İzin Günü", options=["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar", "-"], width="small")
                        }
                    )
                    
                    # PERSONEL SİLME BÖLÜMÜ
                    st.divider()
                    with st.expander("🗑️ Personel Silme İşlemleri", expanded=False):
                        st.warning("⚠️ Silme işlemi geri alınamaz! Dikkatli olun.")
                        
                        # Silinebilir personeli filtrele (Admin hariç herkes silinebilir)
                        deletable_pers = pers_df[pers_df['rol'] != 'Admin'].copy()
                        
                        if not deletable_pers.empty:
                            # İsim arama kutusu
                            search_name = st.text_input(
                                "🔍 İsim Ara (Filtreleme için)",
                                placeholder="Örn: Ahmet, Mehmet, vb.",
                                help="Personel adını yazarak filtreleyebilirsiniz"
                            )
                            
                            # Arama filtreleme
                            if search_name:
                                deletable_pers = deletable_pers[
                                    deletable_pers['ad_soyad'].str.contains(search_name, case=False, na=False)
                                ]
                            
                            # Departman kolonu kontrolü (Eski: bolum, Yeni: departman_adi)
                            dept_col = 'departman_adi' if 'departman_adi' in deletable_pers.columns else ('bolum' if 'bolum' in deletable_pers.columns else None)
                            
                            # Gösterilecek kolonları dinamik olarak belirle
                            display_cols = ['id', 'ad_soyad']
                            if dept_col:
                                display_cols.append(dept_col)
                            if 'gorev' in deletable_pers.columns:
                                display_cols.append('gorev')
                            if 'rol' in deletable_pers.columns:
                                display_cols.append('rol')
                            if 'kullanici_adi' in deletable_pers.columns:
                                display_cols.append('kullanici_adi')
                            if 'durum' in deletable_pers.columns:
                                display_cols.append('durum')
                            
                            # Departman ve rol bilgisi ile göster
                            display_df = deletable_pers[display_cols].copy()
                            display_df = display_df.fillna('-')
                            
                            st.caption(f"📋 Silinebilir Personel Sayısı: {len(deletable_pers)}")
                            
                            if not deletable_pers.empty:
                                # Seçim kutusu - ID ile birlikte göster (mükerrer isimler için)
                                if dept_col:
                                    selected_ids = st.multiselect(
                                        "Silmek istediğiniz personeli seçin:",
                                        options=deletable_pers['id'].tolist(),
                                        format_func=lambda x: f"[ID:{x}] {deletable_pers[deletable_pers['id']==x]['ad_soyad'].values[0]} - {deletable_pers[deletable_pers['id']==x][dept_col].values[0]}"
                                    )
                                else:
                                    selected_ids = st.multiselect(
                                        "Silmek istediğiniz personeli seçin:",
                                        options=deletable_pers['id'].tolist(),
                                        format_func=lambda x: f"[ID:{x}] {deletable_pers[deletable_pers['id']==x]['ad_soyad'].values[0]}"
                                    )
                                
                                if selected_ids:
                                    st.info(f"✓ {len(selected_ids)} personel seçildi")
                                    
                                    # Seçilenleri göster - sadece mevcut kolonları kullan
                                    selected_display_cols = ['ad_soyad']
                                    if dept_col:
                                        selected_display_cols.append(dept_col)
                                    if 'gorev' in deletable_pers.columns:
                                        selected_display_cols.append('gorev')
                                    if 'rol' in deletable_pers.columns:
                                        selected_display_cols.append('rol')
                                    if 'kullanici_adi' in deletable_pers.columns:
                                        selected_display_cols.append('kullanici_adi')
                                    
                                    selected_df = deletable_pers[deletable_pers['id'].isin(selected_ids)][selected_display_cols]
                                    st.dataframe(selected_df, use_container_width=True, hide_index=True)
                                    
                                    col_del1, col_del2 = st.columns([1, 3])
                                    with col_del1:
                                        if st.button("🗑️ SEÇİLENLERİ SİL", type="primary", use_container_width=True):
                                            try:
                                                with engine.connect() as conn:
                                                    # ID'leri string olarak birleştir
                                                    ids_str = ','.join(map(str, selected_ids))
                                                    sql = text(f"DELETE FROM personel WHERE id IN ({ids_str})")
                                                    conn.execute(sql)
                                                    conn.commit()
                                                    
                                                    # Cache temizle
                                                    cached_veri_getir.clear()
                                                    get_user_roles.clear()
                                                    get_personnel_hierarchy.clear()
                                                    
                                                    st.success(f"✅ {len(selected_ids)} personel silindi!")
                                                    time.sleep(1)
                                                    st.rerun()
                                            except Exception as del_error:
                                                st.error(f"Silme hatası: {del_error}")
                                    with col_del2:
                                        st.caption("⚠️ Bu işlem geri alınamaz!")
                            else:
                                st.info(f"🔍 '{search_name}' araması için sonuç bulunamadı.")
                        else:
                            st.info("Silinebilir personel bulunamadı. (Sadece Admin korunur)")
                    
                    st.divider()
                    
                    if st.button("💾 Personel Listesini Kaydet", use_container_width=True):
                        # MÜKERRER İSİM KONTROLÜ
                        # ad_soyad sütunundaki boş olmayan değerleri kontrol et
                        ad_soyad_list = edited_pers['ad_soyad'].dropna().tolist()
                        
                        # Duplicate kontrolü
                        duplicates = [name for name in ad_soyad_list if ad_soyad_list.count(name) > 1]
                        unique_duplicates = list(set(duplicates))
                        
                        if unique_duplicates:
                            st.error(f"❌ MÜKERRER KAYIT TESPİT EDİLDİ!")
                            st.warning(f"Aşağıdaki isimler birden fazla kez girilmiş:")
                            for dup_name in unique_duplicates:
                                count = ad_soyad_list.count(dup_name)
                                st.write(f"   • **{dup_name}** ({count} kez)")
                            st.info("💡 Lütfen mükerrer kayıtları düzeltin ve tekrar kaydedin.")
                        else:
                            # İsimden ID'ye geri dönüştür (Veritabanına kaydetmeden önce)
                            # Departman Adı -> ID
                            name_to_dept_id = {v: k for k, v in dept_id_to_name.items()}
                            edited_pers['departman_id'] = edited_pers['departman_adi'].map(name_to_dept_id)
                            
                            # Yönetici Adı -> ID
                            name_to_yonetici_id = {v: k for k, v in yonetici_id_to_name.items()}
                            edited_pers['yonetici_id'] = edited_pers['yonetici_adi'].map(name_to_yonetici_id)
                            
                            # Pozisyon Adı -> Seviye (Sayı)
                            edited_pers['pozisyon_seviye'] = edited_pers['pozisyon_adi'].apply(
                                lambda x: int(x.split(' - ')[0]) if pd.notna(x) and ' - ' in str(x) else 5
                            )
                            
                            # Yardımcı sütunları kaldır (Veritabanına yazılmasın)
                            edited_pers = edited_pers.drop(columns=['departman_adi', 'yonetici_adi', 'pozisyon_adi'], errors='ignore')
                            
                            # DÜZELTME: to_sql ile 'replace' kullanılamaz çünkü view'lar tabloya bağımlı
                            # Çözüm: TRUNCATE + INSERT kullan
                            try:
                                with engine.connect() as conn:
                                    # Önce tüm kayıtları sil (TRUNCATE yerine DELETE - view'ları etkilemez)
                                    conn.execute(text("DELETE FROM personel"))
                                    conn.commit()
                                
                                # Şimdi yeni verileri ekle (append mode)
                                edited_pers.to_sql("personel", engine, if_exists='append', index=False)
                                
                                # Cache'leri temizle
                                cached_veri_getir.clear()
                                get_user_roles.clear()
                                get_personnel_hierarchy.clear()
                                st.success("✅ Personel listesi güncellendi!")
                                time.sleep(1); st.rerun()
                            except Exception as save_error:
                                st.error(f"Kayıt hatası: {save_error}")
                    
                except Exception as e:
                    st.error(f"Personel verisi alınamadı: {e}")


        with tab2:
            st.subheader("🔐 Kullanıcı Yetki ve Şifre Yönetimi")
            
            # Rolleri veritabanından çek (Tüm tab için ortak)
            try:
                roller_df_tab = pd.read_sql("SELECT rol_adi FROM ayarlar_roller WHERE aktif = TRUE ORDER BY id", engine)
                rol_listesi = roller_df_tab['rol_adi'].tolist()
            except:
                rol_listesi = ["Personel", "Vardiya Amiri", "Bölüm Sorumlusu", "Kalite Sorumlusu", "Depo Sorumlusu", "Admin", "Genel Koordinatör"]
            
            if not rol_listesi: rol_listesi = ["Personel", "Admin"] # Fallback

            # --- YENİ KULLANICI EKLEME BÖLÜMÜ ---
            with st.expander("➕ Sisteme Yeni Kullanıcı Ekle"):
                # Dinamik bölüm listesini hiyerarşik olarak al (Örn: Üretim > Krema)
                bolum_listesi = get_department_hierarchy()
                if not bolum_listesi:
                    bolum_listesi = ["Üretim", "Depo", "Kalite", "Yönetim"]
                
                # Kullanıcı adı olmayan fabrika personelini çek (potansiyel kullanıcılar)
                try:
                    # TÜM personeli çek (Filtresiz - Kullanıcısı olan/olmayan herkes gelsin)
                    # TÜM alanları çek ki form otomatik doldurulsun
                    fabrika_personel_df = pd.read_sql(
                        """
                        SELECT p.*, 
                               COALESCE(d.bolum_adi, 'Tanımsız') as bolum_adi_display
                        FROM personel p
                        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
                        WHERE p.ad_soyad IS NOT NULL 
                        ORDER BY p.ad_soyad
                        """,
                        engine
                    )
                except Exception as sql_error:
                    st.error(f"⚠️ Personel verisi yüklenirken hata: {sql_error}")
                    # Boş DataFrame oluştur
                    fabrika_personel_df = pd.DataFrame()
                
                # Kaynak seçimi: Mevcut Personelden Seç veya Manuel Giriş
                secim_modu = st.radio(
                    "📋 Kullanıcı Kaynağı",
                    ["🏭 Mevcut Fabrika Personelinden Seç", "✏️ Manuel Giriş"],
                    horizontal=True,
                    key="user_source_radio"
                )
                
                with st.form("new_user_form"):
                    col1, col2 = st.columns(2)
                    
                    # Varsayılan değerler
                    n_departman_id_default = 0
                    n_yonetici_id_default = 0
                    n_pozisyon_seviye_default = 5
                    n_gorev_default = ""
                    
                    if secim_modu == "🏭 Mevcut Fabrika Personelinden Seç" and not fabrika_personel_df.empty:
                        # Mevcut personelden seçim
                        personel_listesi = fabrika_personel_df['ad_soyad'].tolist()
                        secilen_personel = col1.selectbox("👤 Personel Seçin", personel_listesi, key="select_personel")
                        
                        # Seçilen personelin TÜM bilgilerini al
                        secilen_row = fabrika_personel_df[fabrika_personel_df['ad_soyad'] == secilen_personel].iloc[0]
                        
                        # Bilgileri çıkar
                        secilen_bolum = secilen_row.get('bolum_adi_display', 'Tanımsız')
                        mevcut_kullanici = secilen_row.get('kullanici_adi', '')
                        mevcut_rol = secilen_row.get('rol', 'Personel')
                        
                        # Form için varsayılan değerleri ayarla
                        n_departman_id_default = int(secilen_row.get('departman_id', 0)) if pd.notna(secilen_row.get('departman_id')) else 0
                        n_yonetici_id_default = int(secilen_row.get('yonetici_id', 0)) if pd.notna(secilen_row.get('yonetici_id')) else 0
                        n_pozisyon_seviye_default = int(secilen_row.get('pozisyon_seviye', 5)) if pd.notna(secilen_row.get('pozisyon_seviye')) else 5
                        n_gorev_default = str(secilen_row.get('gorev', '')) if pd.notna(secilen_row.get('gorev')) else ''
                        
                        st.info(f"📍 Mevcut Bölüm: **{secilen_bolum}** | Görev: **{n_gorev_default if n_gorev_default else 'Tanımsız'}**")
                        
                        # Eğer zaten kullanıcısı varsa bilgi ver
                        if pd.notna(mevcut_kullanici) and mevcut_kullanici != '':
                            st.warning(f"⚠️ Bu personelin zaten kullanıcı hesabı var: **{mevcut_kullanici}** ({mevcut_rol})")
                            st.caption("Değişiklik yaparsanız kullanıcının şifre ve yetkileri güncellenecektir.")
                        
                        n_ad = secilen_personel
                        is_from_personel = True
                    elif secim_modu == "🏭 Mevcut Fabrika Personelinden Seç" and fabrika_personel_df.empty:
                        st.warning("⚠️ Fabrika personeli bulunamadı. Manuel giriş yapın.")
                        n_ad = col1.text_input("Personel Adı Soyadı")
                        is_from_personel = False
                    else:
                        # Manuel giriş
                        n_ad = col1.text_input("Personel Adı Soyadı")
                        is_from_personel = False
                    
                    # Kullanıcı Adı ve Şifre
                    n_user = col2.text_input("🔑 Kullanıcı Adı (Giriş İçin)")
                    n_pass = col1.text_input("🔒 Şifre", type="password")
                    
                    # Rol seçimi (rol_listesi yukarıdan geliyor)
                    n_rol = col2.selectbox("🎭 Yetki Rolü", rol_listesi)
                    
                    st.divider()
                    st.caption("🏢 Organizasyonel Bilgiler (YENİ)")
                    
                    # Departman Seçimi (Foreign Key)
                    try:
                        dept_df = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler WHERE aktif = TRUE ORDER BY sira_no", engine)
                        dept_options = {0: "- Seçiniz -"}
                        dept_hierarchy = get_department_hierarchy()
                        
                        # ID'leri eşleştir
                        for _, row in dept_df.iterrows():
                            # Hiyerarşik ismi bul
                            dept_name = row['bolum_adi']
                            # Hiyerarşik listede ara
                            for h_name in dept_hierarchy:
                                if h_name.endswith(dept_name):
                                    dept_options[row['id']] = h_name
                                    break
                            else:
                                dept_options[row['id']] = dept_name
                    except:
                        dept_options = {0: "- Departman Tanımlanmamış -"}
                    
                    n_departman_id = col1.selectbox(
                        "🏭 Departman", 
                        options=list(dept_options.keys()),
                        index=list(dept_options.keys()).index(n_departman_id_default) if n_departman_id_default in dept_options.keys() else 0,
                        format_func=lambda x: dept_options[x],
                        help="Personelin çalıştığı departman"
                    )
                    
                    # Yönetici Seçimi (Self-referencing FK)
                    try:
                        yonetici_df = pd.read_sql("""
                            SELECT id, ad_soyad, gorev, rol 
                            FROM personel 
                            WHERE ad_soyad IS NOT NULL 
                            ORDER BY ad_soyad
                        """, engine)
                        yonetici_options = {0: "- Yok (Üst Düzey Yönetici) -"}
                        for _, row in yonetici_df.iterrows():
                            gorev_info = f" ({row['gorev']})" if pd.notna(row['gorev']) else f" ({row['rol']})"
                            yonetici_options[row['id']] = f"{row['ad_soyad']}{gorev_info}"
                    except:
                        yonetici_options = {0: "- Yok -"}
                    
                    n_yonetici_id = col2.selectbox(
                        "👔 Doğrudan Yönetici",
                        options=list(yonetici_options.keys()),
                        index=list(yonetici_options.keys()).index(n_yonetici_id_default) if n_yonetici_id_default in yonetici_options.keys() else 0,
                        format_func=lambda x: yonetici_options[x],
                        help="Bu personelin bağlı olduğu yönetici"
                    )
                    
                    # Pozisyon Seviyesi
                    seviye_aciklama = {
                        0: "0 - Yönetim Kurulu",
                        1: "1 - Genel Müdür",
                        2: "2 - Müdür",
                        3: "3 - Şef/Koordinatör",
                        4: "4 - Kıdemli Personel",
                        5: "5 - Personel",
                        6: "6 - Stajyer/Yeni"
                    }
                    
                    n_pozisyon_seviye = col1.selectbox(
                        "📊 Pozisyon Seviyesi",
                        options=list(seviye_aciklama.keys()),
                        index=n_pozisyon_seviye_default if n_pozisyon_seviye_default in seviye_aciklama.keys() else 5,
                        format_func=lambda x: seviye_aciklama[x],
                        help="Organizasyon hiyerarşisindeki seviye (0=En üst)"
                    )
                    
                    # Görev (Opsiyonel)
                    n_gorev = col2.text_input("💼 Görev Tanımı (Opsiyonel)", value=n_gorev_default, placeholder="örn: Üretim Vardiya Şefi")
                    
                    if st.form_submit_button("✅ Kullanıcıyı Oluştur", type="primary"):
                        if n_user and n_pass:
                            try:
                                with engine.connect() as conn:
                                    # Departman ve Yönetici ID'lerini hazırla (0 ise NULL)
                                    dept_id_val = None if n_departman_id == 0 else n_departman_id
                                    yonetici_id_val = None if n_yonetici_id == 0 else n_yonetici_id
                                    
                                    if is_from_personel:
                                        # Mevcut personeli güncelle (UPDATE)
                                        sql = """UPDATE personel 
                                                 SET kullanici_adi = :k, sifre = :s, rol = :r, 
                                                     departman_id = :d, yonetici_id = :y, 
                                                     pozisyon_seviye = :p, gorev = :g, durum = 'AKTİF'
                                                 WHERE ad_soyad = :a"""
                                        conn.execute(text(sql), {
                                            "a": n_ad, "k": n_user, "s": n_pass, "r": n_rol,
                                            "d": dept_id_val, "y": yonetici_id_val, 
                                            "p": n_pozisyon_seviye, "g": n_gorev
                                        })
                                    else:
                                        # Yeni kayıt ekle (INSERT)
                                        sql = """INSERT INTO personel 
                                                 (ad_soyad, kullanici_adi, sifre, rol, departman_id, 
                                                  yonetici_id, pozisyon_seviye, gorev, durum) 
                                                 VALUES (:a, :k, :s, :r, :d, :y, :p, :g, 'AKTİF')"""
                                        conn.execute(text(sql), {
                                            "a": n_ad, "k": n_user, "s": n_pass, "r": n_rol,
                                            "d": dept_id_val, "y": yonetici_id_val,
                                            "p": n_pozisyon_seviye, "g": n_gorev
                                        })
                                    conn.commit()
                                    
                                # Cache'leri temizle
                                cached_veri_getir.clear()
                                get_user_roles.clear()
                                get_personnel_hierarchy.clear()
                                
                                st.success(f"✅ {n_user} kullanıcısı başarıyla oluşturuldu!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Kayıt hatası: {e}")
                        else:
                            st.warning("Kullanıcı adı ve şifre zorunludur.")
            
            st.divider()
            
            
            # --- SİSTEM BAKIMI ---
            with st.expander("🛠️ Sistem Bakımı ve Onarım"):
                st.info("Bu bölümdeki işlemler veritabanı yapısında düzeltmeler yapar. Gerekmedikçe kullanmayınız.")
                
                if st.button("🔄 Organizasyon Şeması Görünümünü Düzenle (Pasifleri Gizle)"):
                    try:
                        with engine.connect() as conn:
                            # View SQL'i (Güncel - Pasifleri Gizleyen)
                            sql = """
                            CREATE OR REPLACE VIEW v_organizasyon_semasi AS
                            SELECT 
                                p.id,
                                p.ad_soyad,
                                p.gorev,
                                p.rol,
                                p.pozisyon_seviye,
                                p.yonetici_id,
                                y.ad_soyad as yonetici_adi,
                                d.bolum_adi as departman,
                                d.id as departman_id,
                                p.kullanici_adi,
                                p.durum,
                                p.vardiya,
                                CASE 
                                    WHEN p.yonetici_id IS NULL THEN p.ad_soyad
                                    ELSE y.ad_soyad || ' > ' || p.ad_soyad
                                END as hiyerarsi_yolu
                            FROM personel p
                            LEFT JOIN personel y ON p.yonetici_id = y.id
                            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
                            WHERE p.ad_soyad IS NOT NULL AND p.durum = 'AKTİF'
                            ORDER BY p.pozisyon_seviye, d.sira_no, p.ad_soyad;
                            """
                            
                            # SQLite kontrolü (OR REPLACE desteklemez)
                            db_url = str(engine.url)
                            if "sqlite" in db_url:
                                conn.execute(text("DROP VIEW IF EXISTS v_organizasyon_semasi"))
                                sql = sql.replace("CREATE OR REPLACE VIEW", "CREATE VIEW")
                            
                            conn.execute(text(sql))
                            conn.commit()
                            
                            # Cache temizle
                            get_personnel_hierarchy.clear()
                            
                            st.success("✅ Organizasyon şeması görünümü güncellendi. Artık sistem genelinde sadece AKTİF personel listelenecek.")
                    except Exception as e:
                        st.error(f"İşlem başarısız: {e}")

            st.divider()
            
            # Yetki Kontrolü: Admin Rolü veya Özel İzinli Kişiler
            # Yetki Kontrolü: Admin Rolü veya Özel İzinli Kişiler
            try:
                # Parametre bağlama hatasını önlemek için f-string veya text() kullanımı
                # Güvenlik için parametreli sorgu tercih ediyoruz ama pandas read_sql bazen sorun çıkarıyor
                # Bu yüzden doğrudan connection üzerinden okuma yapacağız
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT rol FROM personel WHERE kullanici_adi = :u"), {"u": st.session_state.user})
                    row = result.fetchone()
                    current_role = row[0] if row else "Personel"
            except Exception as e:
                # Hata durumunda (tablo yoksa vb.) varsayılan rol
                # st.error(f"Rol kontrol hatası: {e}") # Kullanıcıya gösterme
                current_role = "Personel"
            
            if current_role == "Admin" or st.session_state.user in ["Emre ÇAVDAR", "EMRE ÇAVDAR", "Admin", "admin"]:
                try:
                    # Dinamik bölüm listesini hiyerarşik olarak al (Örn: Üretim > Krema)
                    bolum_listesi_edit = get_department_hierarchy()
                    if not bolum_listesi_edit:
                        bolum_listesi_edit = ["Üretim", "Paketleme", "Depo", "Ofis", "Kalite", "Yönetim", "Temizlik"]
                    
                    # Tüm kullanıcıları çek (kullanıcı adı dolu VE boş string olmayanlar)
                    # Departman bilgisini JOIN ile al
                    users_df = pd.read_sql(
                        """
                        SELECT p.kullanici_adi, p.sifre, p.rol, p.ad_soyad, p.gorev, p.durum,
                               COALESCE(d.bolum_adi, 'Tanımsız') as bolum,
                               p.departman_id, p.yonetici_id, p.pozisyon_seviye, p.ise_giris_tarihi
                        FROM personel p
                        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
                        WHERE p.kullanici_adi IS NOT NULL AND p.kullanici_adi != ''
                        """,
                        engine
                    )
                    
                    # Düzenlenecek sütunları seç
                    if not users_df.empty:
                        # Streamlit data_editor için veri tiplerini garantiye alıyoruz
                        # ".0" ile biten float şifreleri temizle (Örn: 9685.0 -> 9685)
                        users_df['sifre'] = users_df['sifre'].astype(str).str.replace(r'\.0$', '', regex=True)
                        
                        edit_df = users_df[['kullanici_adi', 'sifre', 'rol', 'bolum']]
                        
                        edited_users = st.data_editor(
                            edit_df,
                            key="user_editor_main",
                            column_config={
                                "kullanici_adi": st.column_config.TextColumn("Kullanıcı Adı", disabled=True),
                                "sifre": st.column_config.TextColumn("Şifre (Düzenlenebilir)"),
                                "rol": st.column_config.SelectboxColumn(
                                    "Yetki Rolü", 
                                    options=rol_listesi # Dinamik liste (yukarıda çekilmişti veya şimdi çekilecek)
                                ),
                                "bolum": st.column_config.SelectboxColumn(
                                    "Bölüm",
                                    options=bolum_listesi_edit
                                )
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        if st.button("💾 Kullanıcı Ayarlarını Güncelle", use_container_width=True, type="primary"):
                            try:
                                # Context manager ile bağlantıyı otomatik kapat
                                with engine.connect() as conn:
                                    # Değişiklikleri satır satır güncelle (şifre, rol VE bölüm)
                                    for index, row in edited_users.iterrows():
                                        sql = "UPDATE personel SET sifre = :s, rol = :r, bolum = :b WHERE kullanici_adi = :k"
                                        params = {"s": row['sifre'], "r": row['rol'], "b": row['bolum'], "k": row['kullanici_adi']}
                                        conn.execute(text(sql), params)
                                    conn.commit()
                                # Cache Temizle
                                cached_veri_getir.clear()
                                get_user_roles.clear()
                                st.success("✅ Kullanıcı bilgileri başarıyla güncellendi!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Güncelleme hatası: {e}")
                    else:
                        st.info("Sistemde kayıtlı kullanıcı bulunamadı.")
                except Exception as e:
                    st.error(f"Veri yüklenirken hata: {e}")
            else:
                # Yetkisiz Giriş
                st.warning("⚠️ Bu alan (Yetki ve Şifre Yönetimi) sadece **Emre ÇAVDAR** tarafından düzenlenebilir.")
                users_df = pd.read_sql("SELECT kullanici_adi, rol, bolum FROM personel WHERE kullanici_adi IS NOT NULL", engine)
                st.table(users_df)

        with tab3:
            st.subheader("📦 Ürün Tanımlama ve Dinamik Parametreler")
            edited_products = pd.DataFrame() # Hata önleyici başlangıç değeri
            
            # 1. Ana Ürün Listesi (Numune Sayısı Buradan Ayarlanır)
            st.caption("📋 Ürün Listesi ve Numune Adetleri")
            try:
                u_df = veri_getir("Ayarlar_Urunler")
                
                # Migrasyon Desteği: Sütun yoksa ekle (Kaydederken tabloya işlenir)
                if 'sorumlu_departman' not in u_df.columns:
                    u_df['sorumlu_departman'] = None
                
                # Column Config
                edited_products = st.data_editor(
                    u_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_products",
                    column_config={
                        "urun_adi": st.column_config.TextColumn("Ürün Adı", required=True),
                        "sorumlu_departman": st.column_config.SelectboxColumn(
                            "Sorumlu Departman (Hiyerarşik)",
                            options=get_department_hierarchy(), # Üretim > Pataşu gibi tam liste
                            width="medium",
                            help="Bu ürün hangi departmanda üretiliyor? (KPI ve Üretim Girişinde o birime özel görünür)"
                        ),
                        "raf_omru_gun": st.column_config.NumberColumn("Raf Ömrü (Gün)", min_value=1),
                        "numune_sayisi": st.column_config.NumberColumn("Numune Sayısı (Adet)", min_value=1, max_value=20, default=3),
                        "gramaj": st.column_config.NumberColumn("Gramaj (g)"),
                        "olcum1_ad": None, "olcum1_min": None, "olcum1_max": None, # Eski sabit sütunları gizle
                        "olcum2_ad": None, "olcum2_min": None, "olcum2_max": None,
                        "olcum3_ad": None, "olcum3_min": None, "olcum3_max": None
                    }
                )
                
                if st.button("💾 Ana Ürün Listesini Kaydet", use_container_width=True):
                    edited_products.columns = [c.lower().strip() for c in edited_products.columns]
                    edited_products.to_sql("ayarlar_urunler", engine, if_exists='replace', index=False)
                    # Cache Temizle
                    cached_veri_getir.clear()
                    st.success("✅ Ürün listesi güncellendi!")
                    time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"Ürün verisi hatası: {e}")

            st.divider()

            # 1.5 MEVCUT PARAMETRELERİ GÖSTER (YENİ İSTEK)
            with st.expander("📋 Mevcut Tüm Ürün Parametre Listesi (Referans)"):
                try:
                    all_params = pd.read_sql("SELECT urun_adi, parametre_adi, min_deger, max_deger FROM urun_parametreleri ORDER BY urun_adi", engine)
                    if not all_params.empty:
                        st.dataframe(all_params, use_container_width=True, hide_index=True)
                    else:
                        st.info("Henüz tanımlanmış bir parametre yok.")
                except Exception as e:
                    st.warning("Tablo henüz oluşmamış veya veri yok.")

            st.divider()    

            # 2. Parametre Yönetimi (Seçilen Ürün İçin)
            st.subheader("🧪 Ürün Parametreleri (Brix, pH, Sıcaklık vb.)")
            
            try:
                # Güncel ürün listesini al
                if not edited_products.empty and "urun_adi" in edited_products.columns:
                    urun_listesi = edited_products["urun_adi"].dropna().unique().tolist()
                    secilen_urun_param = st.selectbox("Parametrelerini Düzenlemek İçin Ürün Seçiniz:", urun_listesi)
                    
                    if secilen_urun_param:
                        st.info(f"🔧 **{secilen_urun_param}** için kontrol parametrelerini tanımlayın.")
                        
                        # Mevcut parametreleri çek
                        p_sql = text("SELECT * FROM urun_parametreleri WHERE urun_adi = :u")
                        param_df = pd.read_sql(p_sql, engine, params={"u": secilen_urun_param})
                        if param_df.empty:
                            # Boşsa taslak göster
                            param_df = pd.DataFrame({"urun_adi": [secilen_urun_param], "parametre_adi": [""], "min_deger": [0.0], "max_deger": [0.0]})
                        
                        edited_params = st.data_editor(
                            param_df,
                            num_rows="dynamic",
                            use_container_width=True,
                            key=f"editor_params_{secilen_urun_param}",
                            column_config={
                                "id": None, # ID gizle
                                "urun_adi": None, # Ürün adı zaten seçili, gizle veya sabitle
                                "parametre_adi": st.column_config.TextColumn("Parametre (Örn: Brix)", required=True),
                                "min_deger": st.column_config.NumberColumn("Min Hedef", format="%.2f"),
                                "max_deger": st.column_config.NumberColumn("Max Hedef", format="%.2f")
                            }
                        )

                        if st.button(f"💾 {secilen_urun_param} Parametrelerini Kaydet"):
                            with engine.connect() as conn:
                                # Önce bu ürünün eski kayıtlarını sil (Temiz yöntem)
                                del_sql = text("DELETE FROM urun_parametreleri WHERE urun_adi = :u")
                                conn.execute(del_sql, {"u": secilen_urun_param})
                                conn.commit() # KİLİT ÇÖZMEK İÇİN CRITICAL: Transaction'ı kapat ki to_sql yazabilsin.
                            
                            # Yeni veriyi ekle
                            # urun_adi boş gelenleri doldur
                            edited_params["urun_adi"] = secilen_urun_param
                            # Boş satırları temizle
                            edited_params = edited_params[edited_params["parametre_adi"] != ""]
                            
                            if not edited_params.empty:
                                try:
                                    # ID sütunu varsa düşür, auto-increment çalışsın
                                    if "id" in edited_params.columns:
                                        edited_params = edited_params.drop(columns=["id"])
                                    
                                    edited_params.to_sql("urun_parametreleri", engine, if_exists='append', index=False)
                                    # Cache Temizle
                                    cached_veri_getir.clear()
                                    st.success("✅ Parametreler başarıyla kaydedildi!")
                                    conn.commit()
                                    time.sleep(1); st.rerun()
                                except Exception as e:
                                    st.error(f"Parametre kayıt hatası: {e}")
                            else:
                                conn.commit() # Sadece silme yapıldıysa onayla
                                st.warning("Parametre listesi boş kaydedildi.")
                                st.rerun()

            except Exception as e:
                st.error(f"Parametre yükleme hatası: {e}")

        # 🎭 ROL YÖNETİMİ TAB'I
        with tab_rol:
            st.subheader("🎭 Rol Yönetimi")
            st.caption("Sistemdeki rolleri buradan yönetebilirsiniz")
            
            # Yeni Rol Ekleme
            with st.expander("➕ Yeni Rol Ekle"):
                with st.form("new_role_form"):
                    new_rol_adi = st.text_input("Rol Adı", placeholder="örn: Laboratuvar Teknisyeni")
                    new_rol_aciklama = st.text_area("Açıklama", placeholder="Bu rolün görevleri...")
                    
                    if st.form_submit_button("Rolü Ekle"):
                        if new_rol_adi:
                            try:
                                with engine.connect() as conn:
                                    sql = "INSERT INTO ayarlar_roller (rol_adi, aciklama) VALUES (:r, :a)"
                                    conn.execute(text(sql), {"r": new_rol_adi, "a": new_rol_aciklama})
                                    conn.commit()
                                st.success(f"✅ '{new_rol_adi}' rolü eklendi!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Hata: {e}")
                        else:
                            st.warning("Rol adı zorunludur!")
            
            st.divider()
            
            # Mevcut Roller
            st.caption("📋 Mevcut Roller")
            try:
                roller_df = pd.read_sql("SELECT * FROM ayarlar_roller ORDER BY id", engine)
                
                if not roller_df.empty:
                    edited_roller = st.data_editor(
                        roller_df,
                        key="editor_roller",
                        column_config={
                            "id": st.column_config.NumberColumn("ID", disabled=True),
                            "rol_adi": st.column_config.TextColumn("Rol Adı", required=True),
                            "aciklama": st.column_config.TextColumn("Açıklama"),
                            "aktif": st.column_config.CheckboxColumn("Aktif"),
                            "olusturma_tarihi": None  # Gizle
                        },
                        use_container_width=True,
                        hide_index=True,
                        num_rows="dynamic"
                    )
                    
                    if st.button("💾 Rolleri Kaydet", use_container_width=True, type="primary"):
                        try:
                            with engine.connect() as conn:
                                for index, row in edited_roller.iterrows():
                                    if pd.notna(row['id']):
                                        # Mevcut kaydı güncelle
                                        sql = "UPDATE ayarlar_roller SET rol_adi = :r, aciklama = :a, aktif = :act WHERE id = :id"
                                        conn.execute(text(sql), {"r": row['rol_adi'], "a": row['aciklama'], "act": row['aktif'], "id": row['id']})
                                    else:
                                        # Yeni kayıt ekle
                                        sql = "INSERT INTO ayarlar_roller (rol_adi, aciklama, aktif) VALUES (:r, :a, :act)"
                                        conn.execute(text(sql), {"r": row['rol_adi'], "a": row['aciklama'], "act": row['aktif']})
                                conn.commit()
                            # Cache Temizle
                            cached_veri_getir.clear()
                            st.success("✅ Roller güncellendi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
                else:
                    st.info("Henüz rol tanımlanmamış")
            except Exception as e:
                st.error(f"Roller yüklenirken hata: {e}")
            
            # ORTAK SYNC BUTONU
            render_sync_button()
        
        # 🏭 DEPARTMAN YÖNETİMİ TAB'I
        with tab_bolumler:
            st.subheader("🏭 Departman Yönetimi")
            st.caption("Organizasyonel departmanları ve alt birimleri buradan yönetebilirsiniz.")
            
            # --- YARDIMCI FONKSİYONLAR (RECURSIVE) ---
            def get_department_hierarchy_helper(df, parent_id=None, prefix=""):
                """Dataframe içinden hiyerarşik liste (tuple) döndürür: (id, 'Üretim > Temizlik')"""
                items = []
                children = df[df['ana_departman_id'].fillna(0) == (parent_id if parent_id else 0)]
                
                for _, row in children.iterrows():
                    current_name = f"{prefix}{row['bolum_adi']}"
                    items.append((row['id'], current_name))
                    # Altları ara
                    items.extend(get_department_hierarchy_helper(df, row['id'], f"{current_name} > "))
                return items

            # Liste Görünümü için
            def display_department_tree(df, parent_id=None, level=0):
                children = df[df['ana_departman_id'].fillna(0) == (parent_id if parent_id else 0)]
                for _, row in children.iterrows():
                    indent = "&nbsp;" * (level * 8)
                    icon = "🏢" if level == 0 else "👥" if level == 1 else "🔹"
                    st.markdown(f"{indent}{icon} **{row['bolum_adi']}** (ID: {row['id']})")
                    display_department_tree(df, row['id'], level + 1)

            # --- MEVCUT DEPARTMANLARI ÇEK ---
            try:
                # Tüm listeyi çek
                sql_dept = "SELECT * FROM ayarlar_bolumler ORDER BY sira_no"
                bolumler_df = pd.read_sql(sql_dept, engine)
                
                # Dropdown Listesi Hazırla (Full Hiyerarşi)
                # {id: "Üretim > Temizlik > Bulaşıkhane"} formatında
                dept_hierarchy_list = []
                if not bolumler_df.empty:
                    # Parent ID'si NaN olanları 0 kabul edelim işlem kolaylığı için (veya None kontrolü yapalım)
                    # Recursion başlat
                    raw_list = get_department_hierarchy_helper(bolumler_df, parent_id=None)
                    dept_options = {item[0]: item[1] for item in raw_list}
                else:
                    dept_options = {}

            except Exception as e:
                st.error(f"Veri çekme hatası: {e}")
                bolumler_df = pd.DataFrame()
                dept_options = {}

            # --- YENİ DEPARTMAN EKLEME ---
            with st.expander("➕ Yeni Departman / Alt Birim Ekle"):
                with st.form("new_bolum_form"):
                    col1, col2 = st.columns(2)
                    new_bolum_adi = col1.text_input("Departman/Birim Adı", placeholder="örn: BULAŞIKHANE")
                    
                    # Ana Departman Seçimi (Full Hiyerarşi)
                    parent_opts = {0: "- Yok (Ana Departman) -"}
                    parent_opts.update(dept_options)
                    
                    new_ana_dept = col2.selectbox("Bağlı Olduğu Ana Departman", options=list(parent_opts.keys()), 
                                                  format_func=lambda x: parent_opts[x])

                    new_bolum_sira = col1.number_input("Sıra No", min_value=1, value=10, step=1)
                    new_bolum_aciklama = st.text_area("Açıklama", placeholder="Bu birimin görevleri...")
                    
                    if st.form_submit_button("Departmanı Ekle"):
                        if new_bolum_adi:
                            try:
                                with engine.connect() as conn:
                                    pid = None if new_ana_dept == 0 else new_ana_dept
                                    sql = "INSERT INTO ayarlar_bolumler (bolum_adi, ana_departman_id, aktif, sira_no, aciklama) VALUES (:b, :p, TRUE, :s, :a)"
                                    conn.execute(text(sql), {"b": new_bolum_adi.upper(), "p": pid, "s": new_bolum_sira, "a": new_bolum_aciklama})
                                    conn.commit()
                                # Cache'i temizle
                                cached_veri_getir.clear()
                                st.success(f"✅ '{new_bolum_adi}' eklendi!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Hata: {e}")
                        else:
                            st.warning("Departman adı zorunludur!")
            
            st.divider()
            
            # --- MEVCUT DEPARTMANLARI LİSTELE ---
            st.caption("📋 Organizasyon Şeması (Ağaç Görünümü)")
            
            if not bolumler_df.empty:
                with st.container(border=True):
                    display_department_tree(bolumler_df)
                
                st.divider()

                # 2. Düzenleme Tablosu (Flat) - Hiyerarşik isimle gösterelim
                # Dataframe'e 'full_path' kolonu ekleyelim
                display_df = bolumler_df.copy()
                # Mapping yap
                display_df['Tam Yol'] = display_df['id'].map(dept_options)
                
                with st.expander("📝 Listeyi Düzenle (Detaylı)"):
                    edited_bolumler = st.data_editor(
                        display_df,
                        key="editor_bolumler",
                        column_config={
                            "id": st.column_config.NumberColumn("ID", disabled=True),
                            "Tam Yol": st.column_config.TextColumn("Hiyerarşik Ad", disabled=True),
                            "bolum_adi": st.column_config.TextColumn("Birim Adı (Düzenle)", required=True),
                            "ana_departman_id": st.column_config.NumberColumn("Ana Dept ID"),
                            "aktif": st.column_config.CheckboxColumn("Aktif", default=True),
                            "sira_no": st.column_config.NumberColumn("Sıra"),
                            "aciklama": st.column_config.TextColumn("Açıklama")
                        },
                        use_container_width=True,
                        hide_index=True,
                        num_rows="dynamic"
                    )
                    
                    if st.button("💾 Departman Listesini Kaydet", use_container_width=True, type="primary"):
                        try:
                            with engine.connect() as conn:
                                # Data editor dataframe'i direkt to_sql ile basamaz çünkü extra kolonlar var (ana_departman_adi)
                                # Row-by-row update yapalım
                                for idx, row in edited_bolumler.iterrows():
                                    if pd.notna(row['id']):
                                        pid = row['ana_departman_id']
                                        if pd.isna(pid) or pid == 0: pid = None
                                        
                                        sql = text("""
                                            UPDATE ayarlar_bolumler 
                                            SET bolum_adi = :b, ana_departman_id = :p, aktif = :act, sira_no = :s, aciklama = :a 
                                            WHERE id = :id
                                        """)
                                        conn.execute(sql, {
                                            "b": row['bolum_adi'], "p": pid, "act": row['aktif'], 
                                            "s": row['sira_no'], "a": row['aciklama'], "id": row['id']
                                        })
                                    else:
                                        # Yeni eklenen satırlar (ID'si yok)
                                        # (Data editor'de yeni satır ekleme özelliği complex foreign key'lerde zor olabilir,
                                        # genelde form kullanılması daha güvenlidir ama burada basit insert deneyebiliriz)
                                        pass 
                                conn.commit()
                                cached_veri_getir.clear()
                                st.success("✅ Güncellendi!")
                                time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
            else:
                st.info("Henüz departman tanımlanmamış. Yukarıdan ekleyin.")
            
            # ORTAK SYNC BUTONU
            render_sync_button()
        
        
        # 🔑 YETKİ MATRİSİ TAB'I
        with tab_yetki:
            st.subheader("🔑 Yetki Matrisi")
            st.caption("Her rolün modül erişim yetkilerini buradan düzenleyebilirsiniz")
            
            try:
                # Rolleri çek
                roller_list = pd.read_sql("SELECT rol_adi FROM ayarlar_roller WHERE aktif=TRUE ORDER BY rol_adi", engine)
                
                if not roller_list.empty:
                    secili_rol = st.selectbox("Rol Seçin", roller_list['rol_adi'].tolist())
                    
                    # Modül listesi (sabit)
                    moduller = ["Üretim Girişi", "KPI Kontrol", "Personel Hijyen", "Temizlik Kontrol", "Raporlama", "Ayarlar"]
                    
                    # Bu rolün mevcut yetkilerini çek
                    mevcut_yetkiler = pd.read_sql(
                        f"SELECT modul_adi, erisim_turu FROM ayarlar_yetkiler WHERE rol_adi = '{secili_rol}'",
                        engine
                    )
                    
                    # Yetki matrisi oluştur
                    yetki_data = []
                    for modul in moduller:
                        mevcut = mevcut_yetkiler[mevcut_yetkiler['modul_adi'] == modul]
                        if not mevcut.empty:
                            erisim = mevcut.iloc[0]['erisim_turu']
                        else:
                            erisim = "Yok"
                        yetki_data.append({"Modül": modul, "Yetki": erisim})
                    
                    yetki_df = pd.DataFrame(yetki_data)
                    
                    # Düzenlenebilir tablo
                    edited_yetkiler = st.data_editor(
                        yetki_df,
                        key=f"editor_yetki_{secili_rol}",
                        column_config={
                            "Modül": st.column_config.TextColumn("Modül", disabled=True),
                            "Yetki": st.column_config.SelectboxColumn(
                                "Erişim Seviyesi",
                                options=["Yok", "Görüntüle", "Düzenle"],
                                required=True
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    if st.button(f"💾 {secili_rol} Yetkilerini Kaydet", use_container_width=True, type="primary"):
                        try:
                            with engine.connect() as conn:
                                # Önce bu rolün tüm yetkilerini sil
                                conn.execute(text(f"DELETE FROM ayarlar_yetkiler WHERE rol_adi = :r"), {"r": secili_rol})
                                
                                # Yeni yetkileri ekle
                                for _, row in edited_yetkiler.iterrows():
                                    sql = "INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (:r, :m, :e)"
                                    conn.execute(text(sql), {"r": secili_rol, "m": row['Modül'], "e": row['Yetki']})
                                
                                conn.commit()
                            st.success(f"✅ {secili_rol} yetkileri güncellendi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
                else:
                    st.warning("Önce rol tanımlayın!")
            except Exception as e:
                st.error(f"Yetki matrisi yüklenirken hata: {e}")

        # 📍 LOKASYON YÖNETİMİ TAB'I (YENİ)
        with tab_lokasyon:
            st.subheader("📍 Lokasyon Yönetimi (Kat > Bölüm > Hat > Ekipman)")
            st.caption("Fabrika lokasyon hiyerarşisini ve sorumlu departmanları buradan yönetebilirsiniz")
            
            # Departman Listesini Hiyerarşik Çek (Dropdown için)
            lst_bolumler = []
            try:
                b_df = pd.read_sql("SELECT * FROM ayarlar_bolumler WHERE aktif IS TRUE", engine)
                # Helper fonksiyonu burada da tanımlayalım veya global alana taşıyalım. 
                # (Şimdilik tekrar tanımlıyorum, refactor edilebilirdi)
                def get_hierarchy_flat(df, parent_id=None, prefix=""):
                    items = []
                    children = df[df['ana_departman_id'].fillna(0) == (parent_id if parent_id else 0)]
                    for _, row in children.iterrows():
                        current_name = f"{prefix}{row['bolum_adi']}"
                        items.append(current_name)
                        items.extend(get_hierarchy_flat(df, row['id'], f"{current_name} > "))
                    return items

                lst_bolumler = get_hierarchy_flat(b_df)
                if not lst_bolumler:
                     lst_bolumler = ["Üretim", "Depo", "Kalite", "Bakım"]
            except: 
                lst_bolumler = ["Üretim", "Depo", "Kalite", "Bakım"]

            # Lokasyon verilerini çek
            try:
                lok_df = pd.read_sql("SELECT * FROM lokasyonlar ORDER BY tip, sira_no, ad", engine)
            except:
                lok_df = pd.DataFrame()
            
            # Yeni Lokasyon Ekleme
            with st.expander("➕ Yeni Lokasyon Ekle"):
                col1, col2 = st.columns(2)
                # Yeni Tip: 'Hat' eklendi
                new_lok_tip = col1.selectbox("Lokasyon Tipi", ["Kat", "Bölüm", "Hat", "Ekipman"], key="new_lok_tip")
                new_lok_ad = col2.text_input("Lokasyon Adı", key="new_lok_ad")
                
                # Sorumlu Departman Seçimi
                new_lok_dept = col1.selectbox("Sorumlu Departman", ["(Seçiniz)"] + lst_bolumler, key="new_lok_dept")
                
                # Üst lokasyon seçimi Logic
                parent_options = {0: "- Ana Lokasyon -"}
                if not lok_df.empty:
                    if new_lok_tip == "Bölüm":
                        parents = lok_df[lok_df['tip'] == 'Kat']
                    elif new_lok_tip == "Hat":
                        parents = lok_df[lok_df['tip'] == 'Bölüm']
                    elif new_lok_tip == "Ekipman":
                        # Ekipman; Kat, Bölüm veya Hatta bağlanabilir
                        parents = lok_df[lok_df['tip'].isin(['Kat', 'Bölüm', 'Hat'])]
                    else:
                        parents = pd.DataFrame()
                    
                    for _, row in parents.iterrows():
                        icon = '🏢' if row['tip']=='Kat' else '🏭' if row['tip']=='Bölüm' else '🛤️' if row['tip']=='Hat' else '⚙️'
                        parent_options[row['id']] = f"{icon} {row['ad']}"
                
                new_parent = st.selectbox("Üst Lokasyon", options=list(parent_options.keys()), 
                                          format_func=lambda x: parent_options[x], key="new_parent")
                
                if st.button("💾 Lokasyonu Ekle", use_container_width=True):
                    if new_lok_ad:
                        try:
                            dept_val = new_lok_dept if new_lok_dept != "(Seçiniz)" else None
                            with engine.connect() as conn:
                                sql = "INSERT INTO lokasyonlar (ad, tip, parent_id, sorumlu_departman) VALUES (:a, :t, :p, :d)"
                                conn.execute(text(sql), {
                                    "a": new_lok_ad, "t": new_lok_tip, 
                                    "p": None if new_parent == 0 else new_parent,
                                    "d": dept_val
                                })
                                conn.commit()
                            st.success(f"✅ {new_lok_ad} eklendi!")
                            # Cache temizle
                            cached_veri_getir.clear()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Hata: {e}")
                    else:
                        st.warning("Lokasyon adı zorunludur!")
            
            st.divider()
            
            # Mevcut Lokasyonları Göster (Revize Ağaç Görünümü: Kat > Bölüm > Hat > Ekipman)
            if not lok_df.empty:
                st.caption("📋 Mevcut Lokasyon Hiyerarşisi")
                
                # Ağaç yapısını oluştur
                katlar = lok_df[lok_df['tip'] == 'Kat']
                
                for _, kat in katlar.iterrows():
                    with st.container(border=True):
                        # Kat Başlığı
                        st.markdown(f"🏢 **{kat['ad']}**")
                        
                        # Bu katın bölümleri
                        bolumler = lok_df[(lok_df['tip'] == 'Bölüm') & (lok_df['parent_id'] == kat['id'])]
                        for _, bolum in bolumler.iterrows():
                            dept_badge = f" `👤 {bolum['sorumlu_departman']}`" if pd.notna(bolum.get('sorumlu_departman')) else ""
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🏭 **{bolum['ad']}** {dept_badge}")
                            
                            # 1. Bu bölüme bağlı HATLAR
                            hatlar = lok_df[(lok_df['tip'] == 'Hat') & (lok_df['parent_id'] == bolum['id'])]
                            for _, hat in hatlar.iterrows():
                                dept_badge_hat = f" `👤 {hat['sorumlu_departman']}`" if pd.notna(hat.get('sorumlu_departman')) else ""
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🛤️ **{hat['ad']}** {dept_badge_hat}")
                                
                                # Hat altındaki Ekipmanlar
                                ekip_hat = lok_df[(lok_df['tip'] == 'Ekipman') & (lok_df['parent_id'] == hat['id'])]
                                for _, eh in ekip_hat.iterrows():
                                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;⚙️ {eh['ad']}")

                            # 2. Doğrudan Bölüme bağlı EKİPMANLAR (Hatsız)
                            ekip_bolum = lok_df[(lok_df['tip'] == 'Ekipman') & (lok_df['parent_id'] == bolum['id'])]
                            for _, eb in ekip_bolum.iterrows():
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;⚙️ {eb['ad']}")
                
                # Düzenleme tablosu
                with st.expander("📝 Lokasyonları Düzenle (Toplu İşlem)"):
                    edited_lok = st.data_editor(
                        lok_df,
                        key="editor_lokasyonlar",
                        column_config={
                            "id": st.column_config.NumberColumn("ID", disabled=True),
                            "ad": st.column_config.TextColumn("Lokasyon Adı", required=True),
                            "tip": st.column_config.SelectboxColumn("Tip", options=["Kat", "Bölüm", "Hat", "Ekipman"]),
                            "parent_id": st.column_config.NumberColumn("Üst Lok. ID"),
                            "sorumlu_departman": st.column_config.SelectboxColumn("Sorumlu Departman", options=lst_bolumler),
                            "aktif": st.column_config.CheckboxColumn("Aktif"),
                            "sorumlu_id": None,
                            "sira_no": st.column_config.NumberColumn("Sıra"),
                            "created_at": None
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    if st.button("💾 Lokasyonları Kaydet", use_container_width=True, type="primary"):
                        try:
                            with engine.connect() as conn:
                                trans = conn.begin()
                                try:
                                    for idx, row in edited_lok.iterrows():
                                        # Parent ID kontrolü
                                        pid = row['parent_id']
                                        if pd.isna(pid) or pid == 0: pid = None
                                        
                                        # Sorumlu Departman null kontrolü
                                        s_dep = row['sorumlu_departman']
                                        if pd.isna(s_dep) or s_dep == "": s_dep = None
                                        
                                        sql = text("""
                                            UPDATE lokasyonlar 
                                            SET ad = :ad, 
                                                tip = :tip, 
                                                parent_id = :pid, 
                                                sorumlu_departman = :sdep,
                                                aktif = :aktif, 
                                                sira_no = :sira
                                            WHERE id = :id
                                        """)
                                        conn.execute(sql, {
                                            "ad": row['ad'],
                                            "tip": row['tip'],
                                            "pid": pid,
                                            "sdep": s_dep,
                                            "aktif": row['aktif'],
                                            "sira": row['sira_no'],
                                            "id": row['id']
                                        })
                                    trans.commit()
                                    cached_veri_getir.clear()
                                    st.success("✅ Lokasyonlar güncellendi!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    trans.rollback()
                                    st.error(f"Veritabanı hatası: {e}")
                        except Exception as e:
                            st.error(f"Genel hata: {e}")
            else:
                st.info("📍 Henüz lokasyon tanımlanmamış. Yukarıdan yeni lokasyon ekleyin.")
            
            # ORTAK SYNC BUTONU
            render_sync_button()

        # 🔧 PROSES YÖNETİMİ TAB'I (YENİ)
        with tab_proses:
            st.subheader("🔧 Modüler Proses Yönetimi")
            st.caption("Proses tiplerini tanımlayın ve lokasyonlara atayın")
            
            t_proses1, t_proses2 = st.tabs(["📋 Proses Tipleri", "🔗 Lokasyon-Proses Ataması"])
            
            with t_proses1:
                try:
                    proses_df = pd.read_sql("SELECT * FROM proses_tipleri ORDER BY id", engine)
                except:
                    proses_df = pd.DataFrame()
                
                # Yeni Proses Tipi Ekleme
                with st.expander("➕ Yeni Proses Tipi Ekle"):
                    with st.form("new_proses_form"):
                        col1, col2 = st.columns(2)
                        p_kod = col1.text_input("Kod (Benzersiz)", placeholder="BAKIM").upper()
                        p_ad = col2.text_input("Proses Adı", placeholder="Ekipman Bakım Kontrolü")
                        p_ikon = col1.text_input("İkon", placeholder="🔧")
                        p_modul = col2.text_input("İlgili Modül", placeholder="Bakım Modülü")
                        p_aciklama = st.text_area("Açıklama")
                        
                        if st.form_submit_button("Proses Tipini Ekle"):
                            if p_kod and p_ad:
                                try:
                                    with engine.connect() as conn:
                                        sql = "INSERT INTO proses_tipleri (kod, ad, ikon, modul_adi, aciklama) VALUES (:k, :a, :i, :m, :c)"
                                        conn.execute(text(sql), {"k": p_kod, "a": p_ad, "i": p_ikon, "m": p_modul, "c": p_aciklama})
                                        conn.commit()
                                    # Cache Temizle
                                    cached_veri_getir.clear()
                                    st.success(f"✅ {p_ad} eklendi!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Hata (kod kullanılıyor olabilir): {e}")
                            else:
                                st.warning("Kod ve ad zorunludur!")
                
                # Mevcut Proses Tipleri
                if not proses_df.empty:
                    st.caption("📋 Mevcut Proses Tipleri")
                    for _, row in proses_df.iterrows():
                        aktif_badge = "✅" if row.get('aktif', True) else "❌"
                        st.markdown(f"{row.get('ikon', '📋')} **{row['ad']}** ({row['kod']}) {aktif_badge}")
                else:
                    st.info("Henüz proses tipi tanımlanmamış.")
            
            with t_proses2:
                st.info("💡 Lokasyonlara proses atamak için önce lokasyon ve proses tiplerini tanımlayın.")
                
                try:
                    atama_df = pd.read_sql("""
                        SELECT lpa.id, l.ad as lokasyon, pt.ad as proses, lpa.siklik, lpa.aktif
                        FROM lokasyon_proses_atama lpa
                        JOIN lokasyonlar l ON lpa.lokasyon_id = l.id
                        JOIN proses_tipleri pt ON lpa.proses_tipi_id = pt.id
                        ORDER BY l.ad
                    """, engine)
                except:
                    atama_df = pd.DataFrame()
                
                # Yeni Atama
                try:
                    lok_options = pd.read_sql("SELECT id, ad, tip FROM lokasyonlar WHERE aktif=TRUE ORDER BY tip, ad", engine)
                    proses_options = pd.read_sql("SELECT id, ad, ikon FROM proses_tipleri WHERE aktif=TRUE ORDER BY ad", engine)
                except:
                    lok_options = pd.DataFrame()
                    proses_options = pd.DataFrame()
                
                if not lok_options.empty and not proses_options.empty:
                    with st.expander("➕ Yeni Proses Ataması"):
                        with st.form("new_atama_form"):
                            lok_dict = {row['id']: f"{'🏢' if row['tip']=='Kat' else '🏭' if row['tip']=='Bölüm' else '⚙️'} {row['ad']}" for _, row in lok_options.iterrows()}
                            proses_dict = {row['id']: f"{row.get('ikon', '')} {row['ad']}" for _, row in proses_options.iterrows()}
                            
                            a_lok = st.selectbox("Lokasyon", options=list(lok_dict.keys()), format_func=lambda x: lok_dict[x])
                            a_proses = st.selectbox("Proses", options=list(proses_dict.keys()), format_func=lambda x: proses_dict[x])
                            a_siklik = st.selectbox("Sıklık", ["Her Vardiya", "Günlük", "Haftalık", "Aylık", "3 Aylık", "Her Kullanım", "Yıllık"])
                            
                            if st.form_submit_button("Atamayı Kaydet"):
                                try:
                                    with engine.connect() as conn:
                                        # UPSERT: Varsa güncelle, yoksa ekle
                                        sql = """
                                            INSERT INTO lokasyon_proses_atama (lokasyon_id, proses_tipi_id, siklik) 
                                            VALUES (:l, :p, :s)
                                            ON CONFLICT (lokasyon_id, proses_tipi_id) 
                                            DO UPDATE SET siklik = :s
                                        """
                                        conn.execute(text(sql), {"l": a_lok, "p": a_proses, "s": a_siklik})
                                        conn.commit()
                                    # Cache Temizle
                                    cached_veri_getir.clear()
                                    st.success("✅ Atama kaydedildi/güncellendi!")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Hata: {e}")
                
                # Mevcut Atamalar
                if not atama_df.empty:
                    st.caption("📋 Mevcut Atamalar")
                    st.dataframe(atama_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Henüz proses ataması yok.")


        with tab_tanimlar:
            st.subheader("🧹 Master Temizlik Planı ve Tanımları")
            st.info("Burada fabrikanın temizlik anayasasını (Master Plan) oluşturun. Lokasyon, Ekipman, Yöntem ve Kimyasal ilişkilerini kurun.")
            
            # Alt Sekmeler
            t_plan, t_metot, t_kimyasal = st.tabs(["📅 Master Temizlik Planı", "📝 Metotlar", "🧪 Kimyasallar"])
            
            # --- 1. MASTER TEMİZLİK PLANI ---
            with t_plan:
                st.subheader("MASTER TEMİZLİK PLANI")
                st.caption("Fabrikanın temizlik haritasını katmanlı olarak oluşturun.")
                
                try:
                    # Mevcut Plan Verisini Çek
                    # Görüntüleme için Kat ve Bölüm adlarını da joinleyerek almak en iyisi
                    plan_query = """
                        SELECT 
                            tp.id,
                            k.ad as kat_adi,
                            l.ad as bolum_adi,
                            CASE 
                                WHEN tp.ekipman_id IS NOT NULL THEN e.ad 
                                ELSE tp.yapisal_alan 
                            END as temizlenen_alan,
                            tp.temizlik_turu,
                            tp.siklik,
                            tp.sorumlu_rol as uygulayici,
                            tp.kontrol_rol as kontrolor,
                            c.kimyasal_adi,
                            m.metot_adi,
                            tp.risk_seviyesi
                        FROM ayarlar_temizlik_plani tp
                        LEFT JOIN lokasyonlar l ON tp.lokasyon_id = l.id
                        LEFT JOIN lokasyonlar k ON l.parent_id = k.id
                        LEFT JOIN lokasyonlar e ON tp.ekipman_id = e.id
                        LEFT JOIN kimyasal_envanter c ON tp.kimyasal_id = c.id
                        LEFT JOIN tanim_metotlar m ON tp.metot_id = m.id
                        ORDER BY k.ad, l.ad
                    """
                    try:
                        master_df = pd.read_sql(plan_query, engine)
                    except:
                        master_df = pd.DataFrame()

                    # YENİ PLAN EKLEME FORMU
                    with st.expander("➕ Yeni Temizlik Planı Ekle", expanded=True):
                        with st.form("new_cleaning_plan_cascade"):
                            # Veri Hazırlığı
                            try:
                                # Tüm lokasyonları çek
                                all_locs = pd.read_sql("SELECT id, ad, tip, parent_id FROM lokasyonlar WHERE aktif=1", engine)
                                
                                # TİP DÖNÜŞÜMLERİ (CRITICAL FIX)
                                # Parent ID null ise 0 yap ve integer'a çevir (Float 1.0 sorunu çözümü)
                                all_locs['parent_id'] = all_locs['parent_id'].fillna(0).astype(int)
                                all_locs['id'] = all_locs['id'].astype(int)
                                
                                if 'tip' not in all_locs.columns: all_locs['tip'] = 'Bölüm'
                                
                                chems = pd.read_sql("SELECT id, kimyasal_adi FROM kimyasal_envanter", engine)
                                methods = pd.read_sql("SELECT id, metot_adi FROM tanim_metotlar", engine)
                            except:
                                all_locs = pd.DataFrame(columns=['id', 'ad', 'tip', 'parent_id'])
                                chems = pd.DataFrame()
                                methods = pd.DataFrame()

                            # --- KADEMELİ SEÇİM (CASCADE) ---
                            c_kat, c_bolum = st.columns(2)
                            
                            # 1. KAT SEÇİMİ
                            # Tip='Kat' olanlar veya parent_id=0 olanlar ana lokasyon sayılabilir
                            katlar = all_locs[all_locs['tip'] == 'Kat']
                            if katlar.empty: # Fallback: Parent'ı 0 olanlar
                                katlar = all_locs[all_locs['parent_id'] == 0]
                                
                            kat_dict = {row['id']: row['ad'] for _, row in katlar.iterrows()}
                            sel_kat_id = c_kat.selectbox("🏢 Kat Seçiniz", options=[0] + list(kat_dict.keys()), format_func=lambda x: kat_dict[x] if x!=0 else "Seçiniz...")
                            
                            # 2. BÖLÜM / HAT SEÇİMİ (Kapsamlı ve Recursive)
                            sel_bolum_id = None
                            
                            if sel_kat_id != 0:
                                # Bu kata bağlı olan tüm alt birimleri bul (Recursive)
                                # Pandas ile basit recursive arama (Derinlikli)
                                
                                def get_all_children(df, parent_ids):
                                    children = df[df['parent_id'].isin(parent_ids)]
                                    if not children.empty:
                                        grand_children = get_all_children(df, children['id'].tolist())
                                        return pd.concat([children, grand_children])
                                    return children
                                
                                relevant_units = get_all_children(all_locs, [sel_kat_id])
                                
                                # Sadece Bölüm veya Hat olanları filtrele (Ekipmanlar burada gelmesin)
                                units_filtered = relevant_units[relevant_units['tip'].isin(['Bölüm', 'Hat'])]
                                
                                # Tekrarları temizle
                                units_filtered = units_filtered.drop_duplicates(subset=['id']).sort_values('ad')
                                
                                bolum_dict = {row['id']: f"{row['tip']} - {row['ad']}" for _, row in units_filtered.iterrows()}
                                
                                sel_bolum_id = c_bolum.selectbox("🏭 Bölüm / Hat Seçiniz", options=list(bolum_dict.keys()), format_func=lambda x: bolum_dict[x]) if bolum_dict else None
                                
                                if not bolum_dict: 
                                    c_bolum.info("Bu katta 'Bölüm' veya 'Hat' bulunamadı.")
                            else:
                                c_bolum.selectbox("🏭 Bölüm / Hat Seçiniz", ["Önce Kat Seçin"], disabled=True)

                            # 3. ALAN TİPİ ve SEÇİMİ
                            st.divider()
                            c_tip, c_alan = st.columns([1, 2])
                            alan_tipi = c_tip.radio("Temizlenecek Unsur", ["Ekipman / Makine", "Yapısal Alan (Zemin/Duvar)"], horizontal=True)
                            
                            sel_ekipman_id = None
                            sel_yapisal = None
                            
                            if sel_bolum_id:
                                if alan_tipi == "Ekipman / Makine":
                                    ekipmanlar = all_locs[(all_locs['tip'] == 'Ekipman') & (all_locs['parent_id'] == sel_bolum_id)]
                                    ekip_dict = {row['id']: row['ad'] for _, row in ekipmanlar.iterrows()}
                                    sel_ekipman_id = c_alan.selectbox("⚙️ Ekipman Seçiniz", options=list(ekip_dict.keys()), format_func=lambda x: ekip_dict[x]) if ekip_dict else None
                                    if not ekip_dict: c_alan.warning("Bu bölümde tanımlı ekipman yok.")
                                else:
                                    # Yapısal Alanlar (Statik Liste)
                                    yapisal_list = ["Zemin", "Duvarlar", "Tavan", "Kapılar", "Pencereler", "Aydınlatma Armatürleri", "Havalandırma Izgaraları", "Giderler / Drenaj", "Raflar / Dolaplar", "Elektrik Panoları (Dış)"]
                                    sel_yapisal = c_alan.selectbox("🧱 Yapısal Alan", yapisal_list)
                            else:
                                c_alan.selectbox("Detay", ["Önce Bölüm Seçin"], disabled=True)

                            st.divider()
                            
                            # DİĞER DETAYLAR (Yan Yana)
                            col1, col2, col3 = st.columns(3)
                            
                            roles = ["Temizlik Personeli", "Operatör", "Bakımcı", "Kalite Kontrol", "Yönetici", "Dış Tedarikçi"]
                            sel_role = col1.selectbox("Uygulayıcı Rol", roles, index=0)
                            sel_ctrl = col2.selectbox("Kontrol Eden", roles, index=3) # Kalite varsayılan
                            sel_risk = col3.selectbox("Risk Seviyesi", ["Düşük", "Orta", "Yüksek"])

                            col4, col5, col6 = st.columns(3)
                            sel_freq = col4.selectbox("Sıklık", ["Her Vardiya", "Günlük", "Haftalık", "Aylık", "3 Aylık", "Yıllık", "Üretim Sonrası", "İhtiyaç Halinde"])
                            
                            chem_dict = {row['id']: row['kimyasal_adi'] for _, row in chems.iterrows()}
                            # ID check for FALLBACK
                            sel_chem = col5.selectbox("Kimyasal", options=[0] + list(chem_dict.keys()), format_func=lambda x: chem_dict[x] if x!=0 else "Yok")
                            
                            meth_dict = {row['id']: row['metot_adi'] for _, row in methods.iterrows()}
                            sel_meth = col6.selectbox("Yöntem", options=[0] + list(meth_dict.keys()), format_func=lambda x: meth_dict[x] if x!=0 else "Standart")

                            col7, col8 = st.columns(2)
                            sel_valid = col7.selectbox("Validasyon Sıklığı", ["-", "Her Yıkama", "Günlük", "Haftalık", "Aylık"])
                            sel_verif = col8.selectbox("Verifikasyon (Doğrulama)", ["Görsel Kontrol", "ATP", "Swap", "Allerjen Kit", "Mikrobiyolojik Analiz"])

                            if st.form_submit_button("Planı Kaydet"):
                                if sel_bolum_id and (sel_ekipman_id or sel_yapisal):
                                    try:
                                        with engine.connect() as conn:
                                            # Tablo Şeması Güncelleme (yapisal_alan ekle)
                                            conn.execute(text("""
                                                CREATE TABLE IF NOT EXISTS ayarlar_temizlik_plani (
                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                    lokasyon_id INTEGER,
                                                    ekipman_id INTEGER,
                                                    yapisal_alan TEXT,
                                                    temizlik_turu TEXT,
                                                    siklik TEXT,
                                                    sorumlu_rol TEXT,
                                                    kontrol_rol TEXT,
                                                    kimyasal_id INTEGER,
                                                    metot_id INTEGER,
                                                    validasyon_siklik TEXT,
                                                    verifikasyon_yontemi TEXT,
                                                    verifikasyon_siklik TEXT,
                                                    risk_seviyesi TEXT
                                                )
                                            """))
                                            
                                            # Sütun kontrolü (yapisal_alan var mı?)
                                            try:
                                                conn.execute(text("SELECT yapisal_alan FROM ayarlar_temizlik_plani LIMIT 1"))
                                            except:
                                                try:
                                                    conn.execute(text("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN yapisal_alan TEXT"))
                                                    conn.commit()
                                                except: pass # SQLite alter kısıtlı olabilir
                                            
                                            ins_sql = """
                                                INSERT INTO ayarlar_temizlik_plani 
                                                (lokasyon_id, ekipman_id, yapisal_alan, temizlik_turu, siklik, sorumlu_rol, kontrol_rol, kimyasal_id, metot_id, verifikasyon_yontemi, validasyon_siklik, risk_seviyesi)
                                                VALUES (:l, :e, :y, :t, :s, :r, :c, :k, :m, :v, :val, :risk)
                                            """
                                            
                                            conn.execute(text(ins_sql), {
                                                "l": sel_bolum_id,
                                                "e": sel_ekipman_id,
                                                "y": sel_yapisal,
                                                "t": "Rutin", # Formda sorulmadıysa default
                                                "s": sel_freq,
                                                "r": sel_role,
                                                "c": sel_ctrl,
                                                "k": None if sel_chem == 0 else sel_chem,
                                                "m": None if sel_meth == 0 else sel_meth,
                                                "v": sel_verif,
                                                "val": sel_valid,
                                                "risk": sel_risk
                                            })
                                            conn.commit()
                                        st.success("✅ Temizlik planı kaydedildi!")
                                        time.sleep(1); st.rerun()
                                    except Exception as e:
                                        st.error(f"Kayıt Hatası: {e}")
                                else:
                                    st.warning("Lütfen Kat, Bölüm ve Alan seçimlerini eksiksiz yapınız.")
                    
                    # PLAN LİSTESİ
                    if not master_df.empty:
                        st.dataframe(master_df, use_container_width=True, hide_index=True)
                        if st.button("🗑️ TÜM PLAN TABLOSUNU SIFIRLA", type="secondary"):
                             with engine.connect() as conn:
                                conn.execute(text("DROP TABLE IF EXISTS ayarlar_temizlik_plani"))
                                conn.commit()
                             st.warning("Tablo silindi."); time.sleep(1); st.rerun()
                    else:
                        st.info("Henüz plan oluşturulmamış.")
                        
                except Exception as e:
                    st.error(f"Master plan modülü hatası: {e}")
            
            # --- 2. METOTLAR ---
            with t_metot:
                st.caption("📝 Temizlik Metotları")
                try:
                    df_met = veri_getir("Tanim_Metotlar")
                    ed_met = st.data_editor(df_met, num_rows="dynamic", key="ed_met", use_container_width=True,
                                            column_config={"metot_adi": st.column_config.TextColumn("Metot Adı", required=True)})
                    if st.button("💾 Metotları Kaydet", key="btn_save_met"):
                        ed_met.to_sql("tanim_metotlar", engine, if_exists='replace', index=False)
                        st.success("Kaydedildi!"); time.sleep(0.5); st.rerun()
                except: st.info("Metot bulunamadı")
                
            # --- 3. KİMYASALLAR ---
            with t_kimyasal:
                st.subheader("🧪 Kimyasal Envanteri")
                
                # Yeni Kimyasal Formu
                with st.expander("➕ Yeni Kimyasal Ekle"):
                    with st.form("kimyasal_add_form"):
                        c1, c2 = st.columns(2)
                        k_adi = c1.text_input("Kimyasal Adı")
                        k_ted = c2.text_input("Tedarikçi")
                        k_msds = c1.text_input("MSDS Link")
                        k_tds = c2.text_input("TDS Link")
                        
                        # SUBMIT BUTTON Formun İÇİNDE
                        k_sub = st.form_submit_button("Kimyasalı Kaydet")
                        
                        if k_sub:
                            if k_adi:
                                try:
                                    with engine.connect() as conn:
                                        conn.execute(text("INSERT INTO kimyasal_envanter (kimyasal_adi, tedarikci, msds_yolu, tds_yolu) VALUES (:k, :t, :m, :d)"),
                                                    {"k": k_adi, "t": k_ted, "m": k_msds, "d": k_tds})
                                        conn.commit()
                                    st.success(f"✅ {k_adi} eklendi!"); time.sleep(1); st.rerun()
                                except Exception as e: st.error(str(e))
                            else:
                                st.warning("İsim gerekli")
                
                # Liste
                try:
                    df_kim = veri_getir("Kimyasal_Envanter")
                    if not df_kim.empty:
                        ed_kim = st.data_editor(df_kim, key="ed_kim", use_container_width=True, num_rows="dynamic", hide_index=True)
                        if st.button("💾 Kimyasalları Kaydet", key="btn_save_kim", use_container_width=True):
                            ed_kim.to_sql("kimyasal_envanter", engine, if_exists='replace', index=False)
                            st.success("Güncellendi!"); time.sleep(1); st.rerun()
                except: st.info("Liste hatası")

            # ORTAK SYNC BUTONU
            render_sync_button()

        # 🛡️ GMP SORU BANKASI TAB'I
        with tab_gmp_soru:
            st.subheader("🛡️ GMP Denetimi - Soru Bankası Yönetimi")
            
            t1, t2, t3 = st.tabs(["📋 Mevcut Sorular", "➕ Yeni Soru Ekle", "📤 Excel İçe Aktar"])
            
            with t1:
                try:
                    qs_df = veri_getir("GMP_Soru_Havuzu")
                    if not qs_df.empty:
                        ed_qs = st.data_editor(
                            qs_df, 
                            num_rows="dynamic", 
                            use_container_width=True,
                            key="ed_gmp_questions_main",
                            column_config={
                                "id": st.column_config.NumberColumn("ID", disabled=True),
                                "kategori": st.column_config.SelectboxColumn("Kategori", options=["Hijyen", "Gıda Savunma", "Operasyon", "Gıda Sahteciliği", "Bina/Altyapı", "Genel"]),
                                "risk_puani": st.column_config.NumberColumn("Risk", min_value=1, max_value=3),
                                "frekans": st.column_config.SelectboxColumn("Frekans", options=["GÜNLÜK", "HAFTALIK", "AYLIK"]),
                                "aktif": st.column_config.CheckboxColumn("Aktif"),
                                "lokasyon_ids": st.column_config.TextColumn("Lokasyon IDleri (örn: 13,19)", help="Virgülle ayırarak lokasyon ID'lerini yazın. Boş bırakırsanız TÜM lokasyonlarda sorulur.")
                            }
                        )
                        st.caption("💡 **İpucu:** Hangi lokasyonun hangi ID'ye sahip olduğunu aşağıdaki listeden görebilirsiniz. Birden fazla lokasyon için `13,19` gibi yazın.")
                        
                        # ID Referans Tablosu (Yeni Lokasyon Hiyerarşisi)
                        with st.expander("🔍 Lokasyon ID Referans Listesi"):
                            try:
                                ref_df = pd.read_sql(text("SELECT id, ad as lokasyon_adi, tip FROM lokasyonlar ORDER BY tip, id"), conn)
                                st.dataframe(ref_df, use_container_width=True, hide_index=True)
                                st.caption("💡 Tip: Kat > Bölüm > Ekipman hiyerarşisi")
                            except: st.write("Lokasyon listesi şu an alınamadı.")

                        if st.button("💾 GMP Sorularını Güncelle"):
                            try:
                                with engine.connect() as conn:
                                    # Şemayı bozmadan verileri güncelle: Önce temizle, sonra ekle
                                    conn.execute(text("DELETE FROM gmp_soru_havuzu"))
                                    ed_qs.to_sql("gmp_soru_havuzu", engine, if_exists='append', index=False)
                                    conn.commit()
                                st.success("✅ Soru bankası güncellendi!"); time.sleep(1); st.rerun()
                            except Exception as e:
                                st.error(f"Güncelleme Hatası: {e}")
                                st.info("💡 Not: Eğer 'id' sütunu hatası alıyorsanız, veritabanı şeması bozulmuş olabilir. SQL fix gerekebilir.")
                    else:
                        st.info("Henüz soru tanımlanmamış.")
                except Exception as e: st.error(f"Tablo hatası: {e}")

            with t2:
                st.info("💡 Lokasyon seçimi opsiyoneldir. Boş bırakırsanız soru TÜM lokasyonlarda sorulur.")
                
                with st.form("new_gmp_q_app"):
                    q_kat = st.selectbox("Kategori", ["Hijyen", "Gıda Savunma", "Operasyon", "Gıda Sahteciliği", "Bina/Altyapı", "Genel"])
                    q_txt = st.text_area("Soru Metni")
                    
                    c1, c2, c3 = st.columns(3)
                    q_risk = c1.selectbox("Risk Puanı", [1, 2, 3])
                    q_freq = c2.selectbox("Frekans", ["GÜNLÜK", "HAFTALIK", "AYLIK"])
                    q_brc = c3.text_input("BRC Ref")
                    
                    # Lokasyon Multi-Select (tanim_bolumler'den çek - merkezi sistem)
                    try:
                        lok_options_df = veri_getir("Tanim_Bolumler")
                        if not lok_options_df.empty:
                            # ID'leri ve isimleri mapleyelim
                            lok_dict = {row['id']: f"{row['id']} - {row['bolum_adi']}" for _, row in lok_options_df.iterrows()}
                            selected_loks = st.multiselect(
                                "🗺️ Hangi Bölümlerde Sorulacak?",
                                options=list(lok_dict.keys()),
                                format_func=lambda x: lok_dict.get(x, f"ID: {x}"),
                                help="Boş bırakırsanız TÜM bölümlerde sorulur"
                            )
                        else:
                            selected_loks = []
                            st.warning("⚠️ Henüz bölüm tanımlanmamış. Önce 'Temizlik & Bölümler' tabından bölümleri ekleyip kaydedin.")
                            if st.button("🔄 Listeyi Yenile"):
                                st.rerun()
                    except Exception as e:
                        selected_loks = []
                        st.error(f"Lokasyon listesi yüklenemedi: {e}")
                    
                    if st.form_submit_button("Soru Kaydet"):
                        if q_txt:
                            # Lokasyon ID'lerini virgülle birleştir (örn: "1,2,3")
                            lok_ids_str = ','.join(map(str, selected_loks)) if selected_loks else None
                            
                            with engine.connect() as conn:
                                sql = "INSERT INTO gmp_soru_havuzu (kategori, soru_metni, risk_puani, brc_ref, frekans, lokasyon_ids) VALUES (:k, :s, :r, :b, :f, :l)"
                                conn.execute(text(sql), {"k":q_kat, "s":q_txt, "r":q_risk, "b":q_brc, "f":q_freq, "l":lok_ids_str})
                                conn.commit()
                            st.success("Soru eklendi."); st.rerun()

            with t3:
                st.subheader("📤 Excel'den Toplu Soru Yükleme")
                st.info("""
                    **Dosya Formatı Şöyle Olmalı:**
                    - **KATEGORİ:** (Örn: Hijyen, Operasyon)
                    - **SORU METNİ:** (Örn: Un eleği sağlam mı?)
                    - **RİSK PUANI:** (1, 2 veya 3)
                    - **BRC REF:** (Örn: 4.10.1)
                    - **FREKANS:** (GÜNLÜK, HAFTALIK, AYLIK)
                """)
                
                uploaded_file = st.file_uploader("GMP Soru Listesini Seçin", type=['xlsx', 'csv'], key="gmp_excel_upload")
                if uploaded_file:
                    try:
                        if uploaded_file.name.endswith('.xlsx'):
                            df_imp = pd.read_excel(uploaded_file)
                        else:
                            df_imp = pd.read_csv(uploaded_file)
                        
                        st.write("Önizleme (İlk 5 Satır):", df_imp.head())
                        
                        if st.button("🚀 Verileri Sisteme Yükle"):
                            # Akıllı Sütun Bulma Mantığı
                            cols = {str(c).upper().strip(): c for c in df_imp.columns}
                            
                            def find_col(keywords):
                                for k, original_name in cols.items():
                                    for kw in keywords:
                                        if kw in k: return original_name
                                return None

                            # Sütunları Mapleyelim
                            col_map = {
                                "kategori": find_col(['KATEGORİ', 'KATEGORI', 'CATEGORY', 'GRUP']),
                                "soru": find_col(['SORU', 'METNİ', 'METNI', 'TEXT', 'QUESTION']),
                                "risk": find_col(['RİSK', 'RISK', 'PUAN']),
                                "brc": find_col(['BRC', 'REF']),
                                "frekans": find_col(['FREKANS', 'FREQUENCY', 'SIKLIK'])
                            }

                            if not col_map["soru"]:
                                st.error(f"❌ Hata: Excel dosyasında 'SORU' sütunu bulunamadı. Mevcut başlıklar: {list(cols.keys())}")
                            else:
                                success_count = 0
                                with engine.connect() as conn:
                                    for _, row in df_imp.iterrows():
                                        # Verileri al
                                        kategori_val = row[col_map["kategori"]] if col_map["kategori"] else "Genel"
                                        soru_val = row[col_map["soru"]]
                                        risk_val = row[col_map["risk"]] if col_map["risk"] else 1
                                        brc_val = row[col_map["brc"]] if col_map["brc"] else ""
                                        frekans_val = row[col_map["frekans"]] if col_map["frekans"] else "GÜNLÜK"

                                        if pd.notna(soru_val) and str(soru_val).strip() != "":
                                            # Risk puanını sayıya çevir
                                            try:
                                                final_risk = int(float(risk_val))
                                            except:
                                                final_risk = 1
                                            
                                            sql = """INSERT INTO gmp_soru_havuzu 
                                                     (kategori, soru_metni, risk_puani, brc_ref, frekans, aktif) 
                                                     VALUES (:k, :s, :r, :b, :f, :a)"""
                                            
                                            params = {
                                                "k": str(kategori_val)[:50],
                                                "s": str(soru_val),
                                                "r": final_risk,
                                                "b": str(brc_val)[:50],
                                                "f": str(frekans_val).upper()[:20],
                                                "a": True
                                            }
                                            conn.execute(text(sql), params)
                                            success_count += 1
                                    conn.commit()
                                
                                if success_count > 0:
                                    st.success(f"✅ {success_count} adet soru başarıyla yüklendi!"); time.sleep(1); st.rerun()
                                else:
                                    st.warning("⚠️ Dosya okundu ama geçerli soru bulunamadı.")
                    except Exception as e:
                        st.error(f"Yükleme sırasında hata oluştu: {e}")

            # ORTAK SYNC BUTONU
            render_sync_button()





# --- UYGULAMAYI BAŞLAT ---
if __name__ == "__main__":
    if st.session_state.logged_in:
        main_app()
    else:
        login_screen()