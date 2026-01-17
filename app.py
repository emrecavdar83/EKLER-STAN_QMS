import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import pytz

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

/* 2. Header Branding Temizliği */
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0) !important;
}

/* Sadece deploy butonunu ve gereksiz ikonları gizle */
.stAppDeployButton,
.stActionButton,
footer {
    display: none !important;
    visibility: hidden !important;
}

/* 3. Menü Butonunu (Hamburger) Her Koşulda Göster */
button[data-testid="stSidebarCollapseButton"], 
button[aria-label="Open sidebar"], 
button[aria-label="Close sidebar"] {
    visibility: visible !important;
    display: flex !important;
    background-color: #8B0000 !important;
    color: white !important;
    border-radius: 8px !important;
    z-index: 9999999 !important;
    opacity: 1 !important;
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

/* 4. MainMenu (Üç Nokta) - Görünür kalsın */
#MainMenu {
    visibility: visible !important;
    display: block !important;
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
        
        # Admin her zaman listede olsun (Backdoor)
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
    """Bölüm Sorumlusu için ürün listesini bölüme göre filtreler"""
    user_rol = st.session_state.get('user_rol', 'Personel')
    user_bolum = st.session_state.get('user_bolum', '')
    
    # Admin ve diğer roller tüm ürünleri görebilir
    if user_rol != 'Bölüm Sorumlusu':
        return urun_df
    
    # Bölüm Sorumlusu sadece kendi bölümünün ürünlerini görsün
    if 'uretim_bolumu' in urun_df.columns and user_bolum:
        filtreli = urun_df[urun_df['uretim_bolumu'].astype(str).str.upper() == str(user_bolum).upper()]
        if filtreli.empty:
            st.warning(f"⚠️ '{user_bolum}' bölümüne tanımlı ürün bulunamadı.")
        return filtreli
    
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
                                             format_func=lambda x: lok_df[lok_df['id']==x]['lokasyon_adi'].values[0])
                
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
                                durum = c2.radio("Durum", ["UYGUN", "UYGUN DEĞİL"], key=f"gmp_q_{q_key_id}", horizontal=True)
                                
                                # Risk 3 Mantığı: Uygun değilse zorunlu alanlar
                                foto = None
                                notlar = ""
                                if durum == "UYGUN DEĞİL":
                                    if soru['risk_puani'] == 3:
                                        st.warning("🚨 KRİTİK BULGU! Fotoğraf ve açıklama zorunludur.")
                                        foto = st.file_uploader("⚠️ Fotoğraf Çek/Yükle", type=['jpg','png','jpeg'], key=f"foto_{soru['id']}")
                                    
                                    notlar = st.text_area("Hata Açıklaması / Düzeltici Faaliyet", key=f"not_{soru['id']}")

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
        p_list = pd.read_sql("SELECT ad_soyad, bolum, vardiya, durum FROM personel WHERE ad_soyad IS NOT NULL", engine)
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
            "🧹 Temizlik Takip Raporu"
        ])

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
            "📍 Lokasyonlar",  # YENİ: Kat-Bölüm-Ekipman Hiyerarşisi
            "🔧 Prosesler",    # YENİ: Modüler Proses Yönetimi
            "🧹 Temizlik & Bölümler",
            "🛡️ GMP Sorular"
        ])
        
        with tab1:
            st.subheader("👷 Fabrika Personel Listesi Yönetimi")
            try:
                # Dinamik bölüm listesini al
                bolum_df = veri_getir("Ayarlar_Bolumler")
                bolum_listesi = bolum_df['bolum_adi'].tolist() if not bolum_df.empty else ["Üretim", "Paketleme", "Depo", "Ofis", "Kalite"]
                
                # Tüm tabloyu çek
                pers_df = pd.read_sql("SELECT * FROM personel", engine)
                
                # Düzenlenebilir Editör
                # Gizlenecek teknik sütunları config ile saklıyoruz (şifre, rol, kullanıcı adı admin panelinde yönetilsin)
                edited_pers = st.data_editor(
                    pers_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_personel_main",
                    column_config={
                        "kullanici_adi": None, # Gizle
                        "sifre": None,         # Gizle
                        "rol": None,           # Gizle
                        "ad_soyad": st.column_config.TextColumn("Adı Soyadı", required=True),
                        "bolum": st.column_config.SelectboxColumn("Bölüm", options=bolum_listesi),
                        "gorev": st.column_config.TextColumn("Görevi"),
                        "vardiya": st.column_config.SelectboxColumn("Vardiya", options=["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"]),
                        "durum": st.column_config.SelectboxColumn("Durum", options=["AKTİF", "PASİF"]),
                        "ise_giris_tarihi": st.column_config.DateColumn("İşe Giriş Tarihi", format="DD/MM/YYYY"),
                        "sorumlu_bolum": st.column_config.TextColumn("Sorumlu Bölüm"),
                        "izin_gunu": st.column_config.SelectboxColumn("İzin Günü", options=["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar", "-"])
                    }
                )
                
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
                        # Duplicate yoksa kaydet
                        edited_pers.to_sql("personel", engine, if_exists='replace', index=False)
                        # Cache'i temizle
                        cached_veri_getir.clear()
                        get_user_roles.clear()
                        st.success("✅ Personel listesi güncellendi!")
                        time.sleep(1); st.rerun()
                    
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
                # Dinamik bölüm listesini al
                bolum_df = veri_getir("Ayarlar_Bolumler")
                bolum_listesi = bolum_df['bolum_adi'].tolist() if not bolum_df.empty else ["Üretim", "Depo", "Kalite", "Yönetim"]
                
                # Kullanıcı adı olmayan fabrika personelini çek (potansiyel kullanıcılar)
                try:
                    # TÜM personeli çek (Filtresiz - Kullanıcısı olan/olmayan herkes gelsin)
                    fabrika_personel_df = pd.read_sql(
                        "SELECT ad_soyad, bolum, kullanici_adi, rol FROM personel WHERE ad_soyad IS NOT NULL ORDER BY ad_soyad",
                        engine
                    )
                except:
                    fabrika_personel_df = pd.DataFrame()
                
                # Kaynak seçimi: Mevcut Personelden Seç veya Manuel Giriş
                secim_modu = st.radio(
                    "📋 Kullanıcı Kaynağı",
                    ["🏭 Mevcut Fabrika Personelinden Seç", "✏️ Manuel Giriş"],
                    horizontal=True,
                    key="user_source_radio"
                )
                
                with st.form("new_user_form"):
                    if secim_modu == "🏭 Mevcut Fabrika Personelinden Seç" and not fabrika_personel_df.empty:
                        # Mevcut personelden seçim
                        personel_listesi = fabrika_personel_df['ad_soyad'].tolist()
                        secilen_personel = st.selectbox("👤 Personel Seçin", personel_listesi, key="select_personel")
                        
                        # Seçilen personelin bilgilerini al
                        secilen_row = fabrika_personel_df[fabrika_personel_df['ad_soyad'] == secilen_personel].iloc[0]
                        secilen_bolum = secilen_row['bolum']
                        mevcut_kullanici = secilen_row['kullanici_adi']
                        mevcut_rol = secilen_row['rol']
                        
                        st.info(f"📍 Mevcut Bölüm: **{secilen_bolum if pd.notna(secilen_bolum) else 'Tanımsız'}**")
                        
                        # Eğer zaten kullanıcısı varsa bilgi ver
                        if pd.notna(mevcut_kullanici) and mevcut_kullanici != '':
                            st.warning(f"⚠️ Bu personelin zaten kullanıcı hesabı var: **{mevcut_kullanici}** ({mevcut_rol})")
                            st.caption("Değişiklik yaparsanız kullanıcının şifre ve yetkileri güncellenecektir.")
                        
                        n_ad = secilen_personel
                        n_bolum = secilen_bolum if pd.notna(secilen_bolum) else bolum_listesi[0] if bolum_listesi else "Üretim"
                        is_from_personel = True
                    elif secim_modu == "🏭 Mevcut Fabrika Personelinden Seç" and fabrika_personel_df.empty:
                        st.warning("⚠️ Kullanıcı hesabı olmayan fabrika personeli bulunamadı. Manuel giriş yapın.")
                        n_ad = st.text_input("Personel Adı Soyadı")
                        n_bolum = st.selectbox("Bölüm", bolum_listesi)
                        is_from_personel = False
                    else:
                        # Manuel giriş
                        n_ad = st.text_input("Personel Adı Soyadı")
                        n_bolum = st.selectbox("Bölüm", bolum_listesi)
                        is_from_personel = False
                    
                    n_user = st.text_input("🔑 Kullanıcı Adı (Giriş İçin)")
                    n_pass = st.text_input("🔒 Şifre", type="password")
                    
                    # Rol seçimi (rol_listesi yukarıdan geliyor)
                    n_rol = st.selectbox("🎭 Yetki Rolü", rol_listesi)
                    
                    if st.form_submit_button("✅ Kullanıcıyı Oluştur", type="primary"):
                        if n_user and n_pass:
                            try:
                                with engine.connect() as conn:
                                    if is_from_personel:
                                        # Mevcut personeli güncelle (UPDATE - Kullanıcı adı olsa da olmasa da güncelle)
                                        sql = """UPDATE personel 
                                                 SET kullanici_adi = :k, sifre = :s, rol = :r, durum = 'AKTİF'
                                                 WHERE ad_soyad = :a"""
                                        conn.execute(text(sql), {"a": n_ad, "k": n_user, "s": n_pass, "r": n_rol})
                                    else:
                                        # Yeni kayıt ekle (INSERT)
                                        sql = """INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, bolum, durum) 
                                                 VALUES (:a, :k, :s, :r, :b, 'AKTİF')"""
                                        conn.execute(text(sql), {"a": n_ad, "k": n_user, "s": n_pass, "r": n_rol, "b": n_bolum})
                                    conn.commit()
                                st.success(f"✅ {n_user} kullanıcısı başarıyla oluşturuldu!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Kayıt hatası (Kullanıcı adı kullanılıyor olabilir): {e}")
                        else:
                            st.warning("Kullanıcı adı ve şifre zorunludur.")
            
            st.divider()
            
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
                    # Dinamik bölüm listesini al
                    bolum_df = veri_getir("Ayarlar_Bolumler")
                    bolum_listesi_edit = bolum_df['bolum_adi'].tolist() if not bolum_df.empty else ["Üretim", "Paketleme", "Depo", "Ofis", "Kalite", "Yönetim", "Temizlik"]
                    
                    # Tüm kullanıcıları çek (kullanıcı adı dolu VE boş string olmayanlar)
                    # Boş string olanlar 'Yeni Kullanıcı Ekle' listesine düşmeli
                    users_df = pd.read_sql("SELECT * FROM personel WHERE kullanici_adi IS NOT NULL AND kullanici_adi != ''", engine)
                    
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
            
            # 1. Ana Ürün Listesi (Numune Sayısı Buradan Ayarlanır)
            st.caption("📋 Ürün Listesi ve Numune Adetleri")
            try:
                u_df = veri_getir("Ayarlar_Urunler")
                
                # Column Config
                edited_products = st.data_editor(
                    u_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_products",
                    column_config={
                        "urun_adi": st.column_config.TextColumn("Ürün Adı", required=True),
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
                            st.success("✅ Roller güncellendi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
                else:
                    st.info("Henüz rol tanımlanmamış")
            except Exception as e:
                st.error(f"Roller yüklenirken hata: {e}")
        
        # 🏭 DEPARTMAN YÖNETİMİ TAB'I
        with tab_bolumler:
            st.subheader("🏭 Departman Yönetimi")
            st.caption("Organizasyonel departmanları ve alt birimleri buradan yönetebilirsiniz.")
            
            # --- YARDIMCI FONKSİYONLAR (RECURSIVE) ---
            def get_department_hierarchy(df, parent_id=None, prefix=""):
                """Dataframe içinden hiyerarşik liste (tuple) döndürür: (id, 'Üretim > Temizlik')"""
                items = []
                children = df[df['ana_departman_id'].fillna(0) == (parent_id if parent_id else 0)]
                
                for _, row in children.iterrows():
                    current_name = f"{prefix}{row['bolum_adi']}"
                    items.append((row['id'], current_name))
                    # Altları ara
                    items.extend(get_department_hierarchy(df, row['id'], f"{current_name} > "))
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
                    raw_list = get_department_hierarchy(bolumler_df, parent_id=None)
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
            st.subheader("🧹 Temizlik Proses Tanımları")
            st.info("💡 **Not:** Kat, Bölüm ve Ekipman tanımları artık **📍 Lokasyonlar** sekmesinde yapılmaktadır.")
            
            # Metotlar
            st.caption("📝 Temizlik Metotları")
            df_met = veri_getir("Tanim_Metotlar")
            ed_met = st.data_editor(df_met, num_rows="dynamic", key="ed_metotlar", use_container_width=True,
                                    column_config={
                                        "metot_adi": st.column_config.TextColumn("Metot Adı", required=True),
                                        "aciklama": st.column_config.TextColumn("Açıklama")
                                    })
            if st.button("💾 Metotları Kaydet"):
                ed_met.to_sql("tanim_metotlar", engine, if_exists='replace', index=False)
                st.success("Kaydedildi!"); time.sleep(0.5); st.rerun()
            
            st.divider()
            
            # ALT KISIM: Kimyasallar (Tam Genişlik)
            st.subheader("🧪 Kimyasal Envanteri & Belge Yönetimi")
            
            # Yeni Kimyasal Ekleme
            with st.expander("➕ Yeni Kimyasal Ekle"):
                with st.form("kimyasal_form"):
                    col1, col2 = st.columns(2)
                    k_adi = col1.text_input("Kimyasal Adı")
                    k_tedarikci = col2.text_input("Tedarikçi")
                    k_msds_link = col1.text_input("MSDS Link (isteğe bağlı)", placeholder="https://...")
                    k_tds_link = col2.text_input("TDS Link (isteğe bağlı)", placeholder="https://...")
                    
                    if st.form_submit_button("Kimyasalı Kaydet"):
                        if k_adi:
                            try:
                                # Veritabanına ekle
                                with engine.connect() as conn:
                                    sql = "INSERT INTO kimyasal_envanter (kimyasal_adi, tedarikci, msds_yolu, tds_yolu) VALUES (:k, :t, :m, :d)"
                                    conn.execute(text(sql), {"k": k_adi, "t": k_tedarikci, "m": k_msds_link, "d": k_tds_link})
                                    conn.commit()
                                
                                st.success(f"✅ {k_adi} kaydedildi!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Hata: {e}")
                        else:
                            st.warning("Kimyasal adı zorunludur!")
            
            # Mevcut Kimyasallar
            st.caption("📋 Kayıtlı Kimyasallar")
            try:
                df_kim = veri_getir("Kimyasal_Envanter")
                
                if not df_kim.empty:
                    # Düzenlenebilir tablo
                    edited_kim = st.data_editor(
                        df_kim,
                        key="editor_kimyasallar",
                        column_config={
                            "id": st.column_config.NumberColumn("ID", disabled=True),
                            "kimyasal_adi": st.column_config.TextColumn("Kimyasal Adı", required=True),
                            "tedarikci": st.column_config.TextColumn("Tedarikçi"),
                            "msds_yolu": st.column_config.TextColumn("MSDS Link"),
                            "tds_yolu": st.column_config.TextColumn("TDS Link")
                        },
                        use_container_width=True,
                        hide_index=True,
                        num_rows="dynamic"
                    )
                    
                    if st.button("💾 Kimyasalları Kaydet", use_container_width=True, type="primary"):
                        try:
                            edited_kim.to_sql("kimyasal_envanter", engine, if_exists='replace', index=False)
                            st.success("✅ Kimyasallar güncellendi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
                else:
                    st.info("Henüz kimyasal kaydı yok")
            except Exception as e:
                st.error(f"Kimyasal listesi yüklenemedi: {e}")

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





# --- UYGULAMAYI BAŞLAT ---
if __name__ == "__main__":
    if st.session_state.logged_in:
        main_app()
    else:
        login_screen()