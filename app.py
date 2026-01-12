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
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
        return create_engine(db_url)
    else:
        db_url = 'sqlite:///ekleristan_local.db'
        return create_engine(db_url, connect_args={'check_same_thread': False})

engine = init_connection()

# CACHING: Veri çekme işlemini önbelleğe al (TTL: 60 saniye)
# Böylece her tıklamada tekrar tekrar SQL sorgusu atmaz
@st.cache_data(ttl=60)
def cached_veri_getir(tablo_adi):
    # Orijinal veri_getir mantığı buraya
    sql = ""
    try:
        if tablo_adi == "Ayarlar_Personel":
            sql = "SELECT * FROM personel WHERE kullanici_adi IS NOT NULL"
        elif tablo_adi == "Ayarlar_Urunler":
            sql = "SELECT * FROM ayarlar_urunler"
        elif tablo_adi == "Depo_Giris_Kayitlari":
            sql = "SELECT * FROM depo_giris_kayitlari ORDER BY id DESC LIMIT 50"
        elif tablo_adi == "Ayarlar_Fabrika_Personel":
             sql = "SELECT * FROM personel WHERE ad_soyad IS NOT NULL"
        elif tablo_adi == "Ayarlar_Temizlik_Plani":
            sql = "SELECT * FROM ayarlar_temizlik_plani"
        
        if sql == "": return pd.DataFrame()
        
        df = pd.read_sql(sql, engine)
        df.columns = [c.lower().strip() for c in df.columns] 
        return df
    except Exception as e:
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

# Şunun yerine veritabanından dinamik çekilecek:
try:
    with engine.connect() as conn:
        ADMIN_USERS = [r[0] for r in conn.execute(text("SELECT ad_soyad FROM personel WHERE rol IN ('Admin', 'Yönetim') AND ad_soyad IS NOT NULL")).fetchall()]
        CONTROLLER_ROLES = [r[0] for r in conn.execute(text("SELECT ad_soyad FROM personel WHERE rol IN ('Admin', 'Kalite Sorumlusu', 'Vardiya Amiri') AND ad_soyad IS NOT NULL")).fetchall()]
except:
    ADMIN_USERS = ["Admin", "Emre ÇAVDAR", "EMRE ÇAVDAR"]
    CONTROLLER_ROLES = ["Admin", "Kalite Sorumlusu", "Vardiya Amiri", "EMRE ÇAVDAR", "Emre ÇAVDAR"]

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
                        st.success(f"Hoş geldiniz, {user}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Hatalı Şifre!")
                else:
                    st.error("❓ Kullanıcı kaydı bulunamadı.")
            else:
                st.error("⚠️ Sistem şu an sadece Admin girişi kabul ediyor.")

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
        st.title("🏭 Üretim Veri Girişi")
        u_df = veri_getir("Ayarlar_Urunler")
        
        if not u_df.empty:
            with st.form("uretim_form"):
                col1, col2 = st.columns(2)
                tarih = col1.date_input("Tarih", get_istanbul_time())
                vardiya = col1.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"])
                u_df.columns = [c.lower() for c in u_df.columns] # Sütun isimlerini küçük harfe zorlar
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
                
                if not daily_records.empty:
                    # Özet: Bölüm ve Ürüne göre grup
                    summary = daily_records.groupby(['personel', 'urun']).agg({
                        'miktar': 'sum',
                        'fire': 'sum'
                    }).reset_index()
                    
                    summary.columns = ['Kayıt Eden', 'Ürün', 'Toplam Miktar', 'Toplam Fire']
                    
                    st.caption(f"📅 {filter_date} Tarihli Üretim Özeti")
                    st.dataframe(summary, use_container_width=True, hide_index=True)
                    
                    # Genel toplam
                    col_sum1, col_sum2, col_sum3 = st.columns(3)
                    with col_sum1:
                        st.metric("🏭 Toplam Üretim", f"{summary['Toplam Miktar'].sum():,.0f}")
                    with col_sum2:
                        st.metric("🔥 Toplam Fire", f"{summary['Toplam Fire'].sum():,.0f}")
                    with col_sum3:
                        net = summary['Toplam Miktar'].sum() - summary['Toplam Fire'].sum()
                        st.metric("✅ Net Üretim", f"{net:,.0f}")
                else:
                    st.info(f"🔍 {filter_date} tarihinde üretim kaydı bulunamadı.")
            
            st.divider()
            st.subheader("📋 Son Kayıtlar (Detay)")
            st.dataframe(veri_getir("Depo_Giris_Kayitlari"), use_container_width=True)

        else: st.warning("Ürün tanımlı değil. Veri yükleme scriptini çalıştırın.")

    # >>> MODÜL 2: KPI & KALİTE KONTROL <<<
    elif menu == "🍩 KPI & Kalite Kontrol":
        st.title("🍩 Dinamik Kalite Kontrol")
        u_df = veri_getir("Ayarlar_Urunler")
        if not u_df.empty:
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
            # Lokasyonları ve Soruları Çek
            lok_df = pd.read_sql("SELECT * FROM gmp_lokasyonlar", engine)
            
            if not lok_df.empty:
                secili_lok_id = st.selectbox("Denetim Yapılan Bölüm", 
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
                    AND aktif=1
                    AND (
                        lokasyon_ids IS NULL 
                        OR lokasyon_ids LIKE '%{secili_lok_id}%'
                    )
                """
                soru_df = pd.read_sql(soru_sql, engine)
                
                if soru_df.empty:
                    st.warning(f"⚠️ {lok_df[lok_df['id']==secili_lok_id]['lokasyon_adi'].values[0]} için bugün ({', '.join(aktif_frekanslar)}) sorulacak soru bulunmuyor.")
                    st.info("💡 İpucu: Ayarlar → GMP Sorular bölümünden yeni sorular ekleyin ve lokasyon seçimini yapın.")
                else:
                    with st.form("gmp_denetim_formu"):
                        st.subheader(f"📍 {lok_df[lok_df['id']==secili_lok_id]['lokasyon_adi'].values[0]} Denetim Soruları")
                        
                        denetim_verileri = []
                        
                        for idx, soru in soru_df.iterrows():
                            with st.container(border=True):
                                c1, c2 = st.columns([3, 1])
                                c1.markdown(f"**{soru['soru_metni']}**")
                                c1.caption(f"🏷️ Kategori: {soru['kategori']} | 📑 BRC Ref: {soru['brc_ref']} | ⚡ Risk: {soru['risk_puani']}")
                                
                                durum = c2.radio("Durum", ["UYGUN", "UYGUN DEĞİL"], key=f"gmp_q_{soru['id']}", horizontal=True)
                                
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
                                                "l": secili_lok_id, "q": d['soru_id'], "d": d['durum'], "f": foto_adi,
                                                "n": d['notlar'], "b": d['brc'], "r": d['risk']
                                            }
                                            conn.execute(text(sql), params)
                                        conn.commit()
                                    st.success("✅ Denetim başarıyla kaydedildi!"); time.sleep(1.5); st.rerun()
                                except Exception as e:
                                    st.error(f"Kaydetme hatası: {e}")
            else:
                st.warning("Henüz Lokasyon veya Soru tanımlanmamış. Admin panelinden Excel yüklemesi yapınız.")
        except Exception as e:
            st.error(f"Sistem Hatası: {e}")

    # >>> MODÜL 3: PERSONEL HİJYEN (YENİ KART TASARIMI) <<<
    # >>> MODÜL 3: PERSONEL HİJYEN (AKILLI SİSTEM - ESKİ HALİNE DÖNDÜRÜLDÜ) <<<
    elif menu == "🧼 Personel Hijyen":
        st.title("⚡ Akıllı Personel Kontrol Paneli")
        
        # 1. Personel Listesini SQLite'dan Çek
        p_list = pd.read_sql("SELECT ad_soyad, bolum, vardiya, durum FROM personel WHERE ad_soyad IS NOT NULL", engine)
        p_list.columns = ["Ad_Soyad", "Bolum", "Vardiya", "Durum"] # Kodun beklediği büyük harf formatına çevirir
        
        if not p_list.empty:
            # Temizlik ve Filtreleme
            p_list = p_list[p_list['Durum'].astype(str) == "AKTİF"]
            
            c1, c2 = st.columns(2)
            v_sec = c1.selectbox("Vardiya Seçiniz", sorted(p_list['Vardiya'].unique()))
            p_v = p_list[p_list['Vardiya'] == v_sec]
            
            if not p_v.empty:
                b_sec = c2.selectbox("Bölüm Seçiniz", sorted(p_v['Bolum'].unique()))
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
# >>> MODÜL: TEMİZLİK VE SANİTASYON (BURASI TAMİR EDİLDİ) <<<
    elif menu == "🧹 Temizlik Kontrol":
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
                # Listeleri Çek (Selectbox için)
                lst_bolum = pd.read_sql("SELECT bolum_adi FROM tanim_bolumler", engine)['bolum_adi'].tolist()
                lst_ekipman = pd.read_sql("SELECT ekipman_adi FROM tanim_ekipmanlar", engine)['ekipman_adi'].tolist()
                if not lst_bolum: lst_bolum = ["Tanımsız"] # Hata önleyici
                
                try: lst_kimyasal = pd.read_sql("SELECT kimyasal_adi FROM ayarlar_kimyasallar", engine)['kimyasal_adi'].tolist()
                except: lst_kimyasal = []
                
                try: lst_metot = pd.read_sql("SELECT metot_adi FROM tanim_metotlar", engine)['metot_adi'].tolist()
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

                # Düzenlenebilir tablo (Data Editor)
                edited_df = st.data_editor(
                    master_df, 
                    num_rows="dynamic", 
                    use_container_width=True, 
                    hide_index=True,
                    key="master_plan_editor_main",
                    column_config={
                        "kat_bolum": st.column_config.SelectboxColumn("Bölüm", options=lst_bolum, required=True),
                        "yer_ekipman": st.column_config.SelectboxColumn("Ekipman", options=lst_ekipman, required=True),
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
                df = pd.read_sql(f"SELECT * FROM depo_giris_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'", engine)
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
                df = pd.read_sql(f"SELECT * FROM urun_kpi_kontrol WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'", engine)
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
                    uygunsuzluk = df[df['durum'] != 'Uygun']
                    st.error(f"⚠️ Toplam {len(uygunsuzluk)} Hijyen Uygunsuzluğu Tespit Edildi.")
                    
                    if not uygunsuzluk.empty:
                        st.write("🔍 **Uygunsuzluk Detayları**")
                        st.dataframe(uygunsuzluk[['tarih', 'personel', 'bolum', 'durum', 'sebep']], use_container_width=True)
                    
                    st.write("---")
                    st.write("Tüm Kayıtlar:")
                    st.dataframe(df, use_container_width=True)
                else: st.warning("Hijyen kaydı bulunamadı.")

            # 4. TEMİZLİK TAKİP RAPORU
            elif rapor_tipi == "🧹 Temizlik Takip Raporu":
                df = pd.read_sql(f"SELECT * FROM temizlik_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'", engine)
                if not df.empty:
                    st.success(f"✅ Belirtilen tarihlerde {len(df)} temizlik görevi tamamlandı.")
                    bolum_bazli = df.groupby('bolum').size().reset_index(name='Tamamlanan İşlem')
                    st.bar_chart(bolum_bazli.set_index('bolum'))
                    st.dataframe(df, use_container_width=True)
                else: st.warning("Temizlik kaydı bulunamadı.")

    # >>> MODÜL: AYARLAR <<<   
    elif menu == "⚙️ Ayarlar":
        st.title("⚙️ Sistem Ayarları ve Personel Yönetimi")
        
        # Sekmeleri tanımlıyoruz - Gereksiz olanlar kaldırıldı, hiyerarşik Bölümler Temizlik tabında
        tab1, tab2, tab3, tab_rol, tab_yetki, tab_tanimlar, tab_gmp_soru = st.tabs([
            "👥 Personel", 
            "🔐 Kullanıcılar", 
            "📦 Ürünler",
            "🎭 Roller",
            "🔑 Yetkiler",
            "🧹 Temizlik & Bölümler", # Bölümler artık burada merkezi
            "🛡️ GMP Sorular"
        ])
        
        with tab1:
            st.subheader("👷 Fabrika Personel Listesi Yönetimi")
            try:
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
                        "bolum": st.column_config.SelectboxColumn("Bölüm", options=["Üretim", "Paketleme", "Depo", "Ofis", "Kalite"]),
                        "gorev": st.column_config.TextColumn("Görevi"),
                        "vardiya": st.column_config.SelectboxColumn("Vardiya", options=["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"]),
                        "durum": st.column_config.SelectboxColumn("Durum", options=["AKTİF", "PASİF"])
                    }
                )
                
                if st.button("💾 Personel Listesini Kaydet", use_container_width=True):
                    edited_pers.to_sql("personel", engine, if_exists='replace', index=False)
                    st.success("✅ Personel listesi güncellendi!")
                    time.sleep(1); st.rerun()
                    
            except Exception as e:
                st.error(f"Personel verisi alınamadı: {e}")

        with tab2:
            st.subheader("🔐 Kullanıcı Yetki ve Şifre Yönetimi")
            
            # --- YENİ KULLANICI EKLEME BÖLÜMÜ ---
            with st.expander("➕ Sisteme Yeni Kullanıcı Ekle"):
                with st.form("new_user_form"):
                    n_ad = st.text_input("Personel Adı Soyadı")
                    n_user = st.text_input("Kullanıcı Adı (Giriş İçin)")
                    n_pass = st.text_input("Şifre")
                    n_rol = st.selectbox("Yetki Rolü", ["Personel", "Vardiya Amiri", "Kalite Sorumlusu", "Depo Sorumlusu", "Admin"])
                    n_bolum = st.selectbox("Bölüm", ["Üretim", "Depo", "Kalite", "Yönetim"])
                    
                    if st.form_submit_button("Kullanıcıyı Oluştur"):
                        if n_user and n_pass:
                            try:
                                # Context manager ile bağlantıyı otomatik kapat
                                with engine.connect() as conn:
                                    # Çakışma kontrolü için basit insert denemesi veya önce check
                                    sql = """INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, bolum, durum) 
                                             VALUES (:a, :k, :s, :r, :b, 'AKTİF')"""
                                    conn.execute(text(sql), {"a":n_ad, "k":n_user, "s":n_pass, "r":n_rol, "b":n_bolum})
                                    conn.commit()
                                st.success(f"✅ {n_user} kullanıcısı oluşturuldu!"); time.sleep(1); st.rerun()
                            except Exception as e:
                                st.error(f"Kayıt hatası (Kullanıcı adı kullanılıyor olabilir): {e}")
                        else:
                            st.warning("Kullanıcı adı ve şifre zorunludur.")
            
            st.divider()
            
            # Yetki Kontrolü: SADECE EMRE ÇAVDAR
            if st.session_state.user in ["Emre ÇAVDAR", "EMRE ÇAVDAR"]:
                try:
                    # Tüm personeli çek (kullanıcı adı olanlar)
                    users_df = pd.read_sql("SELECT * FROM personel WHERE kullanici_adi IS NOT NULL", engine)
                    
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
                                    options=["Admin", "Kalite Sorumlusu", "Vardiya Amiri", "Personel", "Depo Sorumlusu"]
                                ),
                                "bolum": st.column_config.SelectboxColumn(
                                    "Bölüm",
                                    options=["Üretim", "Paketleme", "Depo", "Ofis", "Kalite", "Yönetim", "Temizlik"]
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
                            edited_roller.to_sql("ayarlar_roller", engine, if_exists='replace', index=False)
                            st.success("✅ Roller güncellendi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
                else:
                    st.info("Henüz rol tanımlanmamış")
            except Exception as e:
                st.error(f"Roller yüklenirken hata: {e}")
        
        # 🏢 BÖLÜM YÖNETİMİ TAB'I

        
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




        with tab_tanimlar:
            st.subheader("🧹 Temizlik Proses Tanımları")
            
            # ÜST SATIR: 3 Sütun (Bölümler, Ekipmanlar, Metotlar)
            c_t1, c_t2, c_t3 = st.columns(3)
            
            with c_t1:
                st.caption("🏭 Bölümler (Hiyerarşik Yapı)")
                st.info("💡 Ana bölümleri önce ekleyin, sonra alt bölümleri tanımlayın. ID otomatik verilir.")
                
                df_bol = pd.read_sql("SELECT * FROM tanim_bolumler", engine)
                
                # Mevcut bölümleri göster (yardımcı tablo)
                if not df_bol.empty and 'id' in df_bol.columns:
                    with st.expander("📋 Mevcut Bölümler ve ID'leri (Üst Bölüm seçerken kullanın)"):
                        helper_df = df_bol[['id', 'bolum_adi']].copy()
                        helper_df.columns = ['ID', 'Bölüm Adı']
                        st.dataframe(helper_df, use_container_width=True, hide_index=True)
                        st.caption("💡 Alt bölüm eklerken, 'Üst Bölüm ID' kolonuna yukarıdaki ID numarasını yazın")
                
                # ID'siz göster (ID otomatik verilecek)
                if 'id' in df_bol.columns and not df_bol.empty:
                    display_df = df_bol[['bolum_adi', 'parent_id']].copy()
                else:
                    display_df = df_bol.copy() if not df_bol.empty else pd.DataFrame(columns=['bolum_adi', 'parent_id'])
                
                # StreamlitAPIException (type mismatch) hatasını önlemek için parent_id'yi string'e zorla
                if 'parent_id' in display_df.columns:
                    display_df['parent_id'] = display_df['parent_id'].apply(lambda x: "" if (pd.isna(x) or x is None) else str(int(float(x))))
                
                ed_bol = st.data_editor(
                    display_df,
                    num_rows="dynamic",
                    key="ed_bolumler",
                    use_container_width=True,
                    column_config={
                        "bolum_adi": st.column_config.TextColumn(
                            "Bölüm Adı",
                            required=True,
                            help="Fabrika bölüm/alan adı"
                        ),
                        "parent_id": st.column_config.TextColumn(
                            "Üst Bölüm ID",
                            help="Ana bölüm ise BOŞ bırakın. Alt bölüm ise yukarıdaki tablodan ID yazın (örn: 6)"
                        )
                    }
                )
                
                if st.button("💾 Bölümleri Kaydet", key="save_bolumler"):
                    try:
                        # parent_id dönüşümü ve validasyonu
                        def convert_parent_id(val):
                            if pd.isna(val) or val == '' or val == 'None':
                                return None
                            val_str = str(val).strip()
                            if val_str == '':
                                return None
                            try:
                                return int(val_str)
                            except (ValueError, TypeError):
                                return None  # Geçersiz değerleri None yap
                        
                        ed_bol['parent_id'] = ed_bol['parent_id'].apply(convert_parent_id)
                        
                        # Mevcut kayıtları sil ve yeniden ekle (ID'ler otomatik verilsin)
                        with engine.connect() as conn:
                            conn.execute(text("DELETE FROM tanim_bolumler"))
                            
                            for _, row in ed_bol.iterrows():
                                p_val = row['parent_id']
                                # Kesinlik için tekrar kontrol: NaN ise None yap
                                if pd.isna(p_val): p_val = None
                                
                                sql = "INSERT INTO tanim_bolumler (bolum_adi, parent_id) VALUES (:b, :p)"
                                conn.execute(text(sql), {"b": row['bolum_adi'], "p": p_val})
                            
                            conn.commit()
                        
                        st.success("Kaydedildi!"); time.sleep(0.5); st.rerun()
                    except Exception as e:
                        st.error(f"Kaydetme hatası: {str(e)}")
                        st.warning("💡 İpucu: 'Üst Bölüm ID' kısmına sadece SAYI yazın (örn: 6) veya boş bırakın")
                
                # Mevcut kayıtları ID ile göster (bilgi için)
                if not df_bol.empty and 'id' in df_bol.columns:
                    with st.expander("🔍 Mevcut Kayıtlar (ID'lerle)"):
                        st.dataframe(df_bol, use_container_width=True)

            with c_t2:
                st.caption("🔧 Ekipmanlar")
                df_ekip = pd.read_sql("SELECT * FROM tanim_ekipmanlar", engine)
                
                try:
                    bolum_listesi = pd.read_sql("SELECT bolum_adi FROM tanim_bolumler", engine)['bolum_adi'].unique().tolist()
                except: bolum_listesi = []

                ed_ekip = st.data_editor(
                    df_ekip, 
                    num_rows="dynamic", 
                    key="ed_ekipmanlar", 
                    use_container_width=True,
                    column_config={
                        "ekipman_adi": st.column_config.TextColumn("Ekipman Adı"),
                        "bagli_bolum": st.column_config.SelectboxColumn("Bağlı Bölüm", options=bolum_listesi)
                    }
                )
                if st.button("💾 Ekipmanları Kaydet"):
                    ed_ekip.to_sql("tanim_ekipmanlar", engine, if_exists='replace', index=False)
                    st.success("Kaydedildi!"); time.sleep(0.5); st.rerun()

            with c_t3:
                st.caption("📝 Metotlar")
                df_met = pd.read_sql("SELECT * FROM tanim_metotlar", engine)
                ed_met = st.data_editor(df_met, num_rows="dynamic", key="ed_metotlar", use_container_width=True)
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
                df_kim = pd.read_sql("SELECT id, kimyasal_adi, tedarikci, msds_yolu, tds_yolu FROM kimyasal_envanter ORDER BY id", engine)
                
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
            
            t1, t2 = st.tabs(["📋 Mevcut Sorular", "➕ Yeni Soru Ekle"])
            
            with t1:
                try:
                    qs_df = pd.read_sql("SELECT * FROM gmp_soru_havuzu", engine)
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
                                "aktif": st.column_config.CheckboxColumn("Aktif")
                            }
                        )
                        if st.button("💾 GMP Sorularını Güncelle"):
                            ed_qs.to_sql("gmp_soru_havuzu", engine, if_exists='replace', index=False)
                            st.success("✅ Soru bankası güncellendi!"); time.sleep(1); st.rerun()
                    else:
                        st.info("Henüz soru tanımlanmamış.")
                except: st.error("Tablo hatası.")

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
                        lok_options_df = pd.read_sql("SELECT id, bolum_adi FROM tanim_bolumler ORDER BY id", engine)
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





# --- UYGULAMAYI BAŞLAT ---
if __name__ == "__main__":
    if st.session_state.logged_in:
        main_app()
    else:
        login_screen()