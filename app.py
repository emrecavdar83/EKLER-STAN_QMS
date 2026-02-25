# Ekleristan QMS - V: 2026-02-24-1535-Atomic-Fix
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
    get_department_tree,
    flatten_department_hierarchy,
    find_excel_column,
    parse_location_ids,
    format_location_ids,
    execute_with_transaction
)

# UI MODULLERI (MODULAR UI)
from ui.soguk_oda_ui import render_sosts_module
import soguk_oda_utils


# --- 1. AYARLAR & VERİTABANI BAĞLANTISI ---

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
# SİSTEM ADMIN OTOMATİK OLUŞTURMA KAPATILDI
# guvenli_admin_olustur()

def auto_fix_data():
    """Bozuk veri kayıtlarını (Örn: Unicode sorunu olan kullanıcı adları) onarır"""
    try:
        with engine.connect() as conn:
            # 1. Mihrimah Ali (ID 182) Fix
            conn.execute(text("""
                UPDATE personel
                SET kullanici_adi = 'mihrimah.ali',
                    rol = 'Personel',
                    vardiya = 'GÜNDÜZ VARDİYASI'
                WHERE id = 182 AND (rol IS NULL OR rol = '')
            """))

            # 2. GENEL VERİ TEMİZLİĞİ (User Request: "Tablo verilerini temizlemek daha temiz olmaz mı?")
            # Personel tablosundaki kritik sütunların başındaki/sonundaki boşlukları temizle
            clean_sqls = [
                "UPDATE personel SET vardiya = TRIM(vardiya) WHERE vardiya IS NOT NULL;",
                "UPDATE personel SET ad_soyad = TRIM(ad_soyad) WHERE ad_soyad IS NOT NULL;",
                "UPDATE personel SET kullanici_adi = TRIM(kullanici_adi) WHERE kullanici_adi IS NOT NULL;",
                "UPDATE ayarlar_bolumler SET bolum_adi = TRIM(bolum_adi) WHERE bolum_adi IS NOT NULL;"
            ]

            for sql in clean_sqls:
                try:
                    conn.execute(text(sql))
                except Exception as e:
                    print(f"Clean Error: {e}") # Bazı eski SQL versiyonlarında TRIM hata verebilir, yoksay

            conn.commit()
    except Exception:
        pass

# Başlangıçta 1 kez çalıştır
auto_fix_data()

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
# DÜZELTME: Veri güncellemelerinin anlık görünmesi için TTL düşürüldü.
@st.cache_data(ttl=1) # 1 saniye cache (Pratikte cache yok ama performans için kısa süreli tutar)
def run_query(query, params=None):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)

@st.cache_data(ttl=3600) # Rol bazlı listeler 1 saat cache'de kalsın
def get_user_roles():
    try:
        with engine.connect() as conn:
            # DÜZELTME: Veritabanı artık BÜYÜK HARF standartında olduğu için sorguları güncelliyoruz.
            # IN clause içindeki değerleri veritabanındaki reel değerlerle eşleştiriyoruz.
            admins = [r[0] for r in conn.execute(text("SELECT ad_soyad FROM personel WHERE UPPER(TRIM(rol)) IN ('ADMIN', 'YÖNETİM') AND ad_soyad IS NOT NULL")).fetchall()]
            controllers = [r[0] for r in conn.execute(text("SELECT ad_soyad FROM personel WHERE UPPER(TRIM(rol)) IN ('ADMIN', 'KALITE SORUMLUSU', 'VARDIYA AMIRI') AND ad_soyad IS NOT NULL")).fetchall()]
            return admins, controllers
    except Exception as e:
        return [], []

@st.cache_data(ttl=600)
def get_department_tree(filter_tur=None):
    """
    Veritabanından departmanları çekip isim listesi döndürür.
    Hiyerarşiyi bozmadan (ebeveyn filtrelense bile çocukları göstererek) çalışır.
    """
    try:
        # A. Veriyi Ham Çek
        try:
            df_dept = run_query("SELECT id, bolum_adi, ana_departman_id, tur FROM ayarlar_bolumler WHERE aktif IS TRUE ORDER BY sira_no")
        except:
            df_dept = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif IS TRUE ORDER BY sira_no")
            df_dept['tur'] = None

        if df_dept.empty: return []

        hierarchy_list = []

        def build(parent_id, current_path, level):
            if level > 5: return

            # Çocukları bul
            if parent_id is None:
                current = df_dept[df_dept['ana_departman_id'].isnull() | (df_dept['ana_departman_id'] == 0) | (df_dept['ana_departman_id'].isna())]
            else:
                current = df_dept[df_dept['ana_departman_id'] == parent_id]

            for _, row in current.iterrows():
                new_path = f"{current_path} > {row['bolum_adi']}" if current_path else row['bolum_adi']

                # FİLTRE KONTROLÜ:
                # Eğer filtre yoksa VEYA bu satırın türü filtreye uyuyorsa listeye ekle
                if not filter_tur or row['tur'] == filter_tur:
                    hierarchy_list.append(new_path)

                # ÖNEMLİ: Alt dallara her zaman in (Ebeveyn elense bile çocuk uyabilir)
                build(row['id'], new_path, level + 1)

        build(None, "", 1)

        # Eğer filtre sonucu çok daraldıysa ve boş kaldıysa (Güvenlik için hepsini döndür)
        if not hierarchy_list and filter_tur:
            return get_department_tree(None)

        return hierarchy_list
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_department_options_hierarchical():
    """Selectbox için hiyerarşik (Dictionary) yapı döndürür: {id: '  ↳ Alt'}"""
    try:
        df_dept = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif IS TRUE ORDER BY sira_no")
        if df_dept.empty:
            return {0: "- Seçiniz -"}

        options = {0: "- Seçiniz -"}

        # Recursive
        def add_to_options(parent_id, level=0):
            if parent_id is None:
                current = df_dept[df_dept['ana_departman_id'].isnull() | (df_dept['ana_departman_id'] == 0)]
            else:
                current = df_dept[df_dept['ana_departman_id'] == parent_id]

            for _, row in current.iterrows():
                d_id = row['id']
                name = row['bolum_adi']

                # Görünüm: Girintili yapı
                # Streamlit selectbox boşlukları trimleyebilir, bu yüzden özel karakter kullanıyoruz
                # Görünüm: Girintili yapı
                # Streamlit selectbox boşlukları trimleyebilir, bu yüzden özel karakter kullanıyoruz
                # DÜZELTME: NBSP yerine normal karakterler kullanalım, invisible sorununu çözmek için.
                indent = ".. " * level
                marker = "↳ " if level > 0 else ""
                full_name = f"{indent}{marker}{name}"

                options[d_id] = full_name

                # Alt departmanlar
                add_to_options(d_id, level + 1)

        add_to_options(None)
        return options
    except:
        return {0: "- Seçiniz -"}

def get_all_sub_department_ids(parent_id):
    """Verilen departman ID ve altındaki tüm departman ID'lerini listeler"""
    try:
        df_dept = run_query("SELECT id, ana_departman_id FROM ayarlar_bolumler WHERE aktif IS TRUE")

        ids = [parent_id]

        def find_children(p_id):
            children = df_dept[df_dept['ana_departman_id'] == p_id]['id'].tolist()
            for child in children:
                ids.append(child)
                find_children(child)

        find_children(parent_id)
        return ids
    except:
        return [parent_id]



from scripts.sync_manager import SyncManager

def render_sync_button(key_prefix="global"):
    """Ayarlar modülü için GÜVENLİ (Upsert) Lokal -> Cloud senkronizasyon butonu"""
    st.markdown("---")
    col_sync1, col_sync2 = st.columns([3, 1])
    with col_sync1:
        st.info("💡 **Akıllı Cloud Sync:** Lokalde yaptığınız değişiklikleri (Yeni ve Güncellenen) canlı sisteme güvenle aktarır. Mevcut verileri silmez.")
        # EŞSİZ KEY: key_prefix ile checkbox ID çakışmasını önle
        dry_run = st.checkbox("Simülasyon Modu (Değişiklik yapmadan test et)", value=False, key=f"{key_prefix}_dry_run")

    with col_sync2:
        btn_label = "🔍 Test Et" if dry_run else "🚀 Canlıya Gönder"
        btn_type = "secondary" if dry_run else "primary"

        # Button key sabit olmalı (time based olmamalı yoksa tıklandığında algılamaz)
        if st.button(btn_label, key=f"{key_prefix}_btn_sync", type=btn_type, use_container_width=True):
            # 1. Ortam Kontrolü
            is_local = 'sqlite' in str(engine.url)
            if not is_local:
                st.warning("⚠️ Zaten Bulut/Canlı veritabanına bağlısınız. Bu işlem sadece Lokalde çalışır.")
                return

            # 3. İşlem Başlat
            mode_text = "SİMÜLASYON" if dry_run else "CANLI AKTARIM"
            with st.status(f"🚀 {mode_text} Başlatılıyor...", expanded=True) as status:
                try:
                    status.write("☁️ Bağlantılar kontrol ediliyor...")

                    # Context Manager ile SyncManager başlat (Otomatik kapanır)
                    with SyncManager() as manager:
                        # Full Sync Çalıştır
                        results = manager.run_full_sync(dry_run=dry_run)

                        total_inserted = 0
                        total_updated = 0

                        for table, stats in results.items():
                            if "error" in stats:
                                status.write(f"❌ {table}: Hata - {stats['message']}")
                            elif stats.get('status') == 'skipped':
                                 # Boş veya atlanan tabloları logda kalabalık etmemek için yazmayabiliriz
                                 pass
                            else:
                                ins = stats.get('inserted', 0)
                                upd = stats.get('updated', 0)
                                total_inserted += ins
                                total_updated += upd

                                if ins > 0 or upd > 0:
                                    status.write(f"📦 {table}: +{ins} Yeni, ✏️ {upd} Güncelleme")
                                else:
                                    status.write(f"✅ {table}: Güncel")

                        status.update(label=f"✅ {mode_text} Tamamlandı!", state="complete", expanded=True)

                        if dry_run:
                            st.info(f"🧪 SİMÜLASYON SONUCU: Toplam **{total_inserted}** yeni kayıt eklenecek, **{total_updated}** kayıt güncellenecek.")
                        else:
                            st.success(f"🎉 İşlem Başarılı! Toplam **{total_inserted}** yeni kayıt eklendi, **{total_updated}** kayıt güncellendi.")
                            if total_inserted > 0 or total_updated > 0:
                                st.toast("Veri transferi başarılı!", icon="✅")
                                time.sleep(1)
                                st.rerun() # Ekranı yenile

                except Exception as e:
                    status.update(label="❌ Genel Hata", state="error")
                    st.error(f"Beklenmeyen hata: {e}")

# Personel Hiyerarşisini Getir (YENİ - Organizasyon Şeması İçin)
@st.cache_data(ttl=5)  # 5 saniye - personel değişikliklerini hızlı göster
def get_personnel_hierarchy():
    """Personel tablosundan organizasyon hiyerarşisini oluşturur (v_organizasyon_semasi view'ından)"""
    # [ONARIM] View yerine doğrudan tabloyu kullan (Veri tutarlılığı için)
    # Eski: df = pd.read_sql("SELECT * FROM v_organizasyon_semasi", engine)

    # Direkt personel tablosundan çek (En güncel veri)
    try:
        df = pd.read_sql("""
            SELECT
                p.id, p.ad_soyad, p.gorev, p.rol,
                COALESCE(d.bolum_adi, 'Tanımsız') as departman_adi,
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

    # 0. Sütun Adı Düzeltme (Canlı/Lokal Uyum)
    # View'de 'departman' olarak gelebilir, ama kod 'departman_adi' bekler
    if 'departman' in df.columns and 'departman_adi' not in df.columns:
        df = df.rename(columns={'departman': 'departman_adi'})

    # 0.1 Pozisyon Adı Oluşturma (Eğer yoksa)
    # View'de olmayabilir, seviye üzerinden constants.py'den çekeceğiz.
    if 'pozisyon_adi' not in df.columns and 'pozisyon_seviye' in df.columns:
        # get_position_name fonksiyonu constants.py'den geliyor
        df['pozisyon_adi'] = df['pozisyon_seviye'].apply(lambda x: get_position_name(int(x)) if pd.notnull(x) else 'Bilinmiyor')

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
        "personel": "SELECT * FROM personel WHERE ad_soyad IS NOT NULL ORDER BY pozisyon_seviye ASC, ad_soyad ASC",
        "Ayarlar_Personel": "SELECT p.*, d.bolum_adi as bolum FROM personel p LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id WHERE p.kullanici_adi IS NOT NULL ORDER BY p.pozisyon_seviye ASC, p.ad_soyad ASC",
        "Ayarlar_Urunler": "SELECT * FROM ayarlar_urunler",
        "Depo_Giris_Kayitlari": "SELECT * FROM depo_giris_kayitlari ORDER BY id DESC LIMIT 50",
        "Ayarlar_Fabrika_Personel": "SELECT * FROM personel WHERE ad_soyad IS NOT NULL ORDER BY pozisyon_seviye ASC, ad_soyad ASC",
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

# --- YENİ VARDİYA SİSTEMİ YARDIMCI FONKSİYONLARI ---
def get_personnel_shift(personel_id, target_date=None):
    """
    Belirli bir personelin verilen tarihteki vardiyasını döndürür.
    Önce personel_vardiya_programi tablosuna bakar, yoksa personel tablosundaki varsayılanı alır.
    """
    if target_date is None:
        target_date = datetime.now().date()

    try:
        # 1. Program tablosunu kontrol et
        sql = text("""
            SELECT vardiya FROM personel_vardiya_programi
            WHERE personel_id = :pid
            AND :tdate BETWEEN baslangic_tarihi AND bitis_tarihi
            ORDER BY id DESC LIMIT 1
        """)
        with engine.connect() as conn:
            res = conn.execute(sql, {"pid": personel_id, "tdate": target_date}).fetchone()
            if res:
                return res[0]

        # 2. Program yoksa, ana personel tablosundan al (Legacy Back-up, eğer sütun kaldırılmadıysa veya NULL ise)
        # Not: Kolon kaldırılsa bile uygulama patlamamalı, default dönmeli
        sql_legacy = text("SELECT vardiya FROM personel WHERE id = :pid")
        with engine.connect() as conn:
            res_legacy = conn.execute(sql_legacy, {"pid": personel_id}).fetchone()
            if res_legacy and res_legacy[0]:
                return res_legacy[0]

    except Exception as e:
        print(f"Shift Error: {e}")

    return "GÜNDÜZ VARDİYASI" # Fallback

def is_personnel_off(personel_id, target_date=None):
    """
    Personelin o gün izinli olup olmadığını kontrol eder.
    """
    if target_date is None:
        target_date = datetime.now().date()

    day_name_tr_map = {
        0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe",
        4: "Cuma", 5: "Cumartesi", 6: "Pazar"
    }
    today_name = day_name_tr_map[target_date.weekday()]

    try:
        # 1. Program tablosunu kontrol et
        sql = text("""
            SELECT izin_gunleri FROM personel_vardiya_programi
            WHERE personel_id = :pid
            AND :tdate BETWEEN baslangic_tarihi AND bitis_tarihi
            ORDER BY id DESC LIMIT 1
        """)
        with engine.connect() as conn:
            res = conn.execute(sql, {"pid": personel_id, "tdate": target_date}).fetchone()
            if res and res[0]:
                return today_name in res[0] # Örn: 'Cumartesi,Pazar' içinde 'Cumartesi' var mı?

        # 2. Legacy kontrol
        sql_legacy = text("SELECT izin_gunu FROM personel WHERE id = :pid")
        with engine.connect() as conn:
            res_legacy = conn.execute(sql_legacy, {"pid": personel_id}).fetchone()
            if res_legacy and res_legacy[0]:
                return res_legacy[0] == today_name

    except Exception:
        pass

    return False

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
                sql = """INSERT INTO depo_giris_kayitlari (tarih, saat, vardiya, kullanici, islem_tipi, urun, lot_no, miktar, fire, notlar, zaman_damgasi)
                         VALUES (:t, :sa, :v, :k, :i, :u, :l, :m, :f, :n, :z)"""
                params = {"t":veri[0], "sa":veri[1], "v":veri[2], "k":veri[3], "i":veri[4], "u":veri[5], "l":veri[6], "m":veri[7], "f":veri[8], "n":veri[9], "z":veri[10]}
                conn.execute(text(sql), params)
                conn.commit()

                # SEÇİCİ CACHE TEMİZLEME: Sadece Depo kayıtları cache'ini temizle
                cached_veri_getir.clear()
                return True

            elif tablo_adi == "Urun_KPI_Kontrol":
                # ... (SQL Kodu) ...
                sql = """INSERT INTO urun_kpi_kontrol (tarih, saat, vardiya, urun, lot_no, stt, numune_no, olcum1, olcum2, olcum3, karar, kullanici, tat, goruntu, notlar, fotograf_yolu)
                         VALUES (:t, :sa, :v, :u, :l, :stt, :num, :o1, :o2, :o3, :karar, :kul, :tat, :gor, :notlar, :foto)"""
                params = {
                    "t": veri[0], "sa": veri[1], "v": veri[2], "u": veri[3],
                    "l": veri[5], "stt": veri[6], "num": veri[7],
                    "o1": veri[8], "o2": veri[9], "o3": veri[10],
                    "karar": veri[11], "kul": veri[12],
                    "tat": veri[16], "gor": veri[17], "notlar": veri[18],
                    "foto": veri[19] if len(veri) > 19 else None
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

# --- 13. ADAM: HİBRİT NAVİGASYON HUB (ÖLÜMSÜZ MENÜ) ---
# Hamburger menü krizini kökten çözer.
if st.session_state.logged_in:
    # Sayfanın en tepesine, sidebar'dan bağımsız menü koyuyoruz.

    # Modül Listesi (Sabit)
    NAV_MODULES = [
        "🏭 Üretim Girişi",
        "🍩 KPI & Kalite Kontrol",
        "🛡️ GMP Denetimi",
        "🧼 Personel Hijyen",
        "🧹 Temizlik Kontrol",
        "📊 Kurumsal Raporlama",
        "❄️ Soğuk Oda Sıcaklıkları",
        "⚙️ Ayarlar"
    ]

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
            # PERFORMANS: Engine objesi hashlenemediği için URL gönderiyoruz (Cache uyumu)
            df_gecikme = soguk_oda_utils.get_overdue_summary(str(engine.url))
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
                        # [GÜNCELLEME] 1. Aktiflik Kontrolü
                        kullanici_durumu = u_data.iloc[0].get('durum')
                        # Eğer durum boşsa varsayılan olarak AKTİF kabul ETMEYELİM, ya da veritabanında düzelttik.
                        # Ama güvenli olması için: Sadece net 'AKTİF' yazanlar girebilsin.
                        if str(kullanici_durumu).strip().upper() not in ['AKTİF', 'TRUE']:
                            st.error(f"⛔ Hesabınız PASİF durumdadır ({kullanici_durumu}). Sistem yöneticiniz ile görüşün.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            # Kullanıcının rol ve bölüm bilgisini kaydet (RBAC için)
                            st.session_state.user_rol = u_data.iloc[0].get('rol', 'Personel')
                            # GÜNCELLEME: Artık join ile gelen 'bolum' sütununu kullanıyoruz
                            raw_bolum = u_data.iloc[0].get('bolum', '')
                            # Eğer duplicate column varsa Series dönebilir, güvenli hale getir
                            if isinstance(raw_bolum, (pd.Series, pd.DataFrame, list)):
                                try:
                                    st.session_state.user_bolum = str(raw_bolum.iloc[0]) if hasattr(raw_bolum, 'iloc') else str(raw_bolum[0])
                                except:
                                    st.session_state.user_bolum = ""
                            else:
                                st.session_state.user_bolum = str(raw_bolum) if raw_bolum else ""

                            # Fallback: Eğer join çalışmadıysa veya boşsa, eski usül departman_id'den bulmaya çalışalım (Opsiyonel)
                            if not st.session_state.user_bolum and 'departman_id' in u_data.columns:
                                try:
                                    d_id = u_data.iloc[0].get('departman_id')
                                    if d_id:
                                        # Bu durumda sorgu atmak cache bozmaz çünkü nadir olur
                                        d_name = run_query(f"SELECT bolum_adi FROM ayarlar_bolumler WHERE id={d_id}").iloc[0,0]
                                        st.session_state.user_bolum = d_name
                                except: pass
                            st.success(f"Hoş geldiniz, {user}!")
                            # Browser sessionStorage'a kullanici adini kaydet
                            # QR tarama sonrasi sayfa reload olunca bu bilgi kurtarilir
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
# Modül isimleri eşlemesi (Menu -> Veritabanı)
MODUL_ESLEME = {
    "🏭 Üretim Girişi": "Üretim Girişi",
    "🍩 KPI & Kalite Kontrol": "KPI Kontrol",
    "🛡️ GMP Denetimi": "GMP Denetimi",
    "🧼 Personel Hijyen": "Personel Hijyen",
    "🧹 Temizlik Kontrol": "Temizlik Kontrol",
    "📊 Kurumsal Raporlama": "Raporlama",
    "❄️ Soğuk Oda Sıcaklıkları": "Soğuk Oda",
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
    # DÜZELTME: İ/I karakter sorunu için her iki varyasyonu da kontrol etmek en güvenlisi
    user_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper()

    # Admin her şeye erişebilir
    if user_rol in ['ADMIN', 'SİSTEM ADMİN']:
        return True

    # Modül adını veritabanı formatına çevir
    modul_adi = MODUL_ESLEME.get(menu_adi, menu_adi)

    # Yetkiyi kontrol et
    erisim = kullanici_yetkisi_getir(user_rol, modul_adi)

    # Eğer yetki bulunamadıysa (Noktalı İ sorunu), Noktasız I ile tekrar dene
    if erisim == "Yok":
        user_rol_alt = user_rol.replace('İ', 'I')
        erisim = kullanici_yetkisi_getir(user_rol_alt, modul_adi)

    if gereken_yetki == "Görüntüle":
        return erisim.upper() in ["GÖRÜNTÜLE", "DÜZENLE"]
    elif gereken_yetki == "Düzenle":
        return erisim.upper() in ["DÜZENLE"]
    return False

def bolum_bazli_urun_filtrele(urun_df):
    """Bölüm Sorumlusu için ürün listesini hiyerarşik olarak filtreler"""
    user_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper()
    user_bolum = st.session_state.get('user_bolum', '')

    # 1. Admin, Üst Yönetim ve Kalite Ekibi her şeyi görsün
    # "Kalite" kelimesi geçen her ROL veya BÖLÜM kapsansın (BÜYÜK HARF KARŞILAŞTIRMA)
    rol_upper = user_rol.upper()
    bolum_upper = str(user_bolum).upper()
    user_id_str = str(st.session_state.user).strip()

    if user_rol in ['ADMIN', 'YÖNETİM', 'GIDA MÜHENDİSİ'] or \
       'KALİTE' in rol_upper or \
       'KALİTE' in bolum_upper or \
       'LABORATUVAR' in bolum_upper or \
       user_id_str == 'sevcanalbas':
        return urun_df

    # 2. Vardiya Amiri Filtresi (Sadece kendi bölümü varsa filtrele, yoksa genel görür)
    if (user_rol in ['VARDIYA AMIRI', 'VARDIYA AMİRİ']) and not user_bolum:
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
            # DÜZELTME: 'None' stringlerini de boş kabul et (Veri hatası önleme)
            mask_bos = urun_df['sorumlu_departman'].isna() | \
                       (urun_df['sorumlu_departman'] == '') | \
                       (urun_df['sorumlu_departman'].astype(str).str.lower() == 'none')

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

        # DEBUG: Sevcan Hanım için rol kontrolü (Geçici)
        if str(st.session_state.user) == 'sevcanalbas':
            st.code(f"Rol: {st.session_state.get('user_rol')}\nBölüm: {st.session_state.get('user_bolum')}")

        st.markdown("---")

        # 13. ADAM PROTOKOLÜ: Navigasyon Senkronizasyonu
        # Hem üstteki Selectbox hem de Sidebar Radio aynı state'i yönetmeli.

        modul_listesi = [
            "🏭 Üretim Girişi",
            "🍩 KPI & Kalite Kontrol",
            "🛡️ GMP Denetimi",
            "🧼 Personel Hijyen",
            "🧹 Temizlik Kontrol",
            "📊 Kurumsal Raporlama",
            "❄️ Soğuk Oda Sıcaklıkları",
            "⚙️ Ayarlar"
        ]

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
            st.cache_data.clear()
            st.cache_resource.clear()
            # Session State Temizliği (Güvenli Loop)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # >>> MODÜL 1: ÜRETİM KAYIT SİSTEMİ <<<
    if menu == "🏭 Üretim Girişi":
        if not kullanici_yetkisi_var_mi(menu, "Düzenle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()

        st.title("🏭 Üretim Kayıt Girişi")
        st.caption("Günlük üretim miktarlarını ve fire detaylarını buradan işleyebilirsiniz.")

        # Ürün Listesini Çek (Teknik Doküman: Ayarlar_Urunler)
        u_df = veri_getir("Ayarlar_Urunler")

        if not u_df.empty:
            # Sütun isimlerini küçült (standardizasyon)
            u_df.columns = [c.lower() for c in u_df.columns]
            # Sorumlu departman filtresi (Teknik dökümana göre iş kuralı 6.2)
            u_df = bolum_bazli_urun_filtrele(u_df)

            with st.form("uretim_giris_form"):
                col1, col2 = st.columns(2)
                f_tarih = col1.date_input("Üretim Tarihi", get_istanbul_time())
                f_saat = col1.text_input("Giriş Saati", get_istanbul_time().strftime("%H:%M"))
                f_vardiya = col1.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"])
                f_urun = col1.selectbox("Üretilen Ürün", u_df['urun_adi'].unique())

                f_lot = col2.text_input("Lot No / Parti No")
                f_miktar = col2.number_input("Üretim Miktarı (Adet/Kg)", min_value=0.0, format="%.2f")
                f_fire = col2.number_input("Fire Miktarı", min_value=0.0, format="%.2f")
                f_not = col2.text_area("Üretim / Fire Detay Notu", help="Üretim detaylarını veya fire nedenlerini buraya detaylıca yazabilirsiniz.", height=150)

                if st.form_submit_button("💾 Üretimi Kaydet", use_container_width=True):
                    if f_lot and f_miktar > 0:
                        # Teknik Doküman Tablo: Depo_Giris_Kayitlari
                        # DÜZELTME: guvenli_kayit_ekle fonksiyonu LIST bekliyor (index 0,1,2...), dict değil.
                        yeni_kayit = [
                            str(f_tarih),
                            f_saat,
                            f_vardiya,
                            st.session_state.user,
                            "URETIM",
                            f_urun,
                            f_lot,
                            f_miktar,
                            f_fire,
                            f_not,
                            str(get_istanbul_time())
                        ]
                        if guvenli_kayit_ekle("Depo_Giris_Kayitlari", yeni_kayit):
                            st.success(f"✅ {f_urun} üretimi başarıyla kaydedildi!"); time.sleep(1); st.rerun()
                    else:
                        st.warning("⚠️ Lütfen Lot No ve Miktar alanlarını doldurun.")

        st.divider()
        st.subheader("📊 Günlük Üretim İzleme")

        # Filtreleme Barı
        f_col1, f_col2 = st.columns([2, 2])
        izleme_tarih = f_col1.date_input("İzleme Tarihi", value=get_istanbul_time().date(), key="prod_view_date")

        # Kayıtları Getir
        records = veri_getir("Depo_Giris_Kayitlari")
        if not records.empty:
            records['tarih'] = pd.to_datetime(records['tarih']).dt.date
            filtered = records[records['tarih'] == izleme_tarih]

            if not filtered.empty:
                # UI'da Teknik Doküman Sütunlarını Sadeleştirerek Göster
                cols_to_show = ['saat', 'vardiya', 'urun', 'lot_no', 'miktar', 'fire', 'kullanici', 'notlar']
                present_cols = [c for c in cols_to_show if c in filtered.columns]
                ui_df = filtered[present_cols].copy()

                # Sütun isimlerini Türkçeleştir
                rename_map = {
                    'saat': 'Saat',
                    'vardiya': 'Vardiya',
                    'urun': 'Ürün Adı',
                    'lot_no': 'Lot No',
                    'miktar': 'Miktar',
                    'fire': 'Fire',
                    'kullanici': 'Kaydeden',
                    'notlar': 'Notlar'
                }
                ui_df.columns = [rename_map.get(c, c) for c in ui_df.columns]
                st.dataframe(ui_df, use_container_width=True, hide_index=True)

                # Toplamlar
                t_mikt = filtered['miktar'].sum()
                t_fire = filtered['fire'].sum()
                st.info(f"📈 Toplam Üretim: {t_mikt:,.2f} | 📉 Toplam Fire: {t_fire:,.2f}")
            else:
                st.info("ℹ️ Seçilen tarihte henüz üretim kaydı bulunmuyor.")
        else:
            st.warning("⚠️ Ürün tanımı bulunamadı. Lütfen Ayarlar > Ürün Yönetimi sayfasından ürün ekleyin.")

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

            if u_df.empty:
                st.warning("⚠️ Bu bölümde tanımlı veya yetkiniz dâhilinde ürün bulunamadı.")
                st.stop()

            c1, c2 = st.columns(2)
            u_df.columns = [c.lower() for c in u_df.columns] # Sütun isimlerini küçük harfe zorlar
            urun_secilen = c1.selectbox("Ürün Seçin", u_df['urun_adi'].unique())

            if not urun_secilen:
                st.warning("Lütfen bir ürün seçiniz.")
                st.stop()

            lot_kpi = c2.text_input("Lot No", placeholder="Üretim Lot No")
            vardiya_kpi = c1.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], key="kpi_v")

            urun_ayar = u_df[u_df['urun_adi'] == urun_secilen].iloc[0]

            # --- DİNAMİK YAPILANDIRMA ---
            try:
                numune_adet = int(float(urun_ayar.get('numune_sayisi', 1) or 1))
            except:
                numune_adet = 1

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

            try:
                raf_omru = int(float(urun_ayar.get('raf_omru_gun', 0) or 0))
            except:
                raf_omru = 0
            stt_date = get_istanbul_time().date() + timedelta(days=raf_omru)
            st.info(f"ℹ {urun_secilen} için Raf Ömrü: {raf_omru} Gün | STT: {stt_date} | Numune Sayısı: {numune_adet}")

            with st.form("kpi_form"):
                # 1. STT ve Etiket Kontrolü (Zorunlu)
                st.subheader("✅ Ön Kontroller")
                stt_ok = st.checkbox("Üretim Tarihi ve Son Tüketim Tarihi (STT) Etiket Bilgisi Doğrudur")
                stt_foto = st.file_uploader("📸 STT Etiket Fotoğrafı (Zorunlu)", type=['jpg','png','jpeg'], key="stt_foto_upload")

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
                    elif not stt_foto:
                        st.error("⛔ Kayıt için STT Etiket fotoğrafı yüklemelisiniz!")
                    else:
                        try:
                            # Fotoğrafı Kaydet
                            os.makedirs("data/uploads/kpi", exist_ok=True)
                            foto_uzanti = stt_foto.name.split('.')[-1]
                            foto_adi = f"stt_{get_istanbul_time().strftime('%Y%m%d_%H%M%S')}.{foto_uzanti}"
                            foto_yolu = f"data/uploads/kpi/{foto_adi}"

                            with open(foto_yolu, "wb") as f:
                                f.write(stt_foto.getbuffer())
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
                                final_not,                      # 18 (Detaylı Veri)
                                foto_adi                        # 19 (Fotoğraf Yolu/Adı)
                            ]

                            if guvenli_kayit_ekle("Urun_KPI_Kontrol", veri_paketi):
                                st.success(f"✅ Analiz kaydedildi. Karar: {karar}")
                                st.caption("Detaylı veriler başarıyla işlendi.")
                                time.sleep(1.5); st.rerun()
                            else:
                                st.error("❌ Kayıt sırasında veritabanı hatası oluştu.")

                        except Exception as e:
                            st.error(f"Beklenmeyen bir hata oluştu: {str(e)}")
                            # Hatanın detayını konsola da yazalım
                            print(f"KPI KAYIT HATASI: {e}")


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
            # 1. Veri Normalizasyonu (Canonicalize)
            p_list['Durum'] = p_list['Durum'].astype(str).str.strip().str.upper()
            p_list['Vardiya'] = p_list['Vardiya'].astype(str).str.strip()
            p_list['Bolum'] = p_list['Bolum'].astype(str).str.strip()

            # Sadece AKTİF personeli getir
            p_list = p_list[p_list['Durum'].astype(str).str.upper() == "AKTİF"]

            c1, c2 = st.columns(2)
            # Filter out NaN/None values and convert to list before sorting
            vardiya_values = [v for v in p_list['Vardiya'].unique() if v and v != 'nan' and v != 'None']
            v_sec = c1.selectbox("Vardiya Seçiniz", sorted(vardiya_values) if vardiya_values else ["GÜNDÜZ VARDİYASI"])
            p_v = p_list[p_list['Vardiya'] == v_sec]

            if not p_v.empty:
                bolum_values = [b for b in p_v['Bolum'].unique() if pd.notna(b)]
                # GÜNCELLEME: Bölüm Sorumlusu için Kendi Bölümünü Otomatik Seçme
                default_bolum_index = 0
                if st.session_state.get('user_bolum'):
                    user_bolum = st.session_state.user_bolum
                    # Bölüm listesinde kullanıcının bölümü var mı kontrol et
                    # (Tam eşleşme veya 'PROFİTEROL' in 'ÜRETİM > PROFİTEROL' gibi)
                    for idx, b_opt in enumerate(sorted(bolum_values)):
                         if str(user_bolum).upper() in str(b_opt).upper():
                             default_bolum_index = idx
                             break

                b_sec = c2.selectbox("Bölüm Seçiniz", sorted(bolum_values) if bolum_values else ["Tanımsız"], index=default_bolum_index)
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
                # 1. Master Plandan Aktif İşleri Çek (Mevcut tablo yapısına uygun basit sorgu)
                query = """
                    SELECT
                        rowid as id,
                        COALESCE(kat, '') as kat_adi,
                        kat_bolum as kat_bolum_full,
                        yer_ekipman as ekipman_alan,
                        siklik,
                        kimyasal as kimyasal_adi,
                        risk as risk_seviyesi,
                        validasyon_siklik,
                        verifikasyon,
                        verifikasyon_siklik,
                        uygulayici,
                        kontrol_eden as kontrol_rol,
                        uygulama_yontemi as metot_detay
                    FROM ayarlar_temizlik_plani
                """
                plan_df = pd.read_sql(query, engine)

                if not plan_df.empty:
                    # Hiyerarşiyi ayrıştır: kat_bolum_full içinden Kat, Bölüm, Hat çıkar
                    # Format: "Kat > Bölüm" veya "Kat > Bölüm > Hat"
                    def parse_hierarchy(row):
                        full = row['kat_bolum_full'] or ""
                        parts = [p.strip() for p in full.split(">")]
                        kat = row['kat_adi'] if row['kat_adi'] else (parts[0] if len(parts) > 0 else "")
                        bolum = parts[1] if len(parts) > 1 else (parts[0] if len(parts) == 1 else "")
                        hat = parts[2] if len(parts) > 2 else ""
                        return pd.Series([kat, bolum, hat])

                    plan_df[['kat_parsed', 'bolum_parsed', 'hat_parsed']] = plan_df.apply(parse_hierarchy, axis=1)

                    # Unique değerleri çek
                    katlar_unique = sorted([k for k in plan_df['kat_parsed'].unique() if k])

                    st.caption("📍 **Denetlenecek Lokasyonu Seçin** (Hiyerarşik Filtreleme)")
                    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])

                    # 1. KAT SEÇİMİ
                    kat_options = ["Tümü"] + katlar_unique
                    sel_kat = c1.selectbox("🏢 Kat", kat_options, key="saha_kat_select")

                    # 2. BÖLÜM SEÇİMİ (Kata göre filtrele)
                    if sel_kat != "Tümü":
                        bolumler_unique = sorted([b for b in plan_df[plan_df['kat_parsed'] == sel_kat]['bolum_parsed'].unique() if b])
                    else:
                        bolumler_unique = sorted([b for b in plan_df['bolum_parsed'].unique() if b])

                    bolum_options = ["Tümü"] + bolumler_unique
                    sel_bolum = c2.selectbox("🏭 Bölüm", bolum_options, key="saha_bolum_select")

                    # 3. HAT SEÇİMİ (Kat ve Bölüme göre filtrele)
                    filtered_for_hat = plan_df.copy()
                    if sel_kat != "Tümü":
                        filtered_for_hat = filtered_for_hat[filtered_for_hat['kat_parsed'] == sel_kat]
                    if sel_bolum != "Tümü":
                        filtered_for_hat = filtered_for_hat[filtered_for_hat['bolum_parsed'] == sel_bolum]

                    hatlar_unique = sorted([h for h in filtered_for_hat['hat_parsed'].unique() if h])

                    if hatlar_unique:
                        hat_options = ["Tümü"] + hatlar_unique
                        sel_hat = c3.selectbox("🛤️ Hat", hat_options, key="saha_hat_select")
                    else:
                        sel_hat = "Tümü"
                        c3.selectbox("🛤️ Hat", ["Hat Yok"], disabled=True, key="saha_hat_disabled")

                    # 4. VARDİYA SEÇİMİ
                    vardiya = c4.selectbox("⏰ Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], key="t_v_apply")

                    # HİYERARŞİK FİLTRELEME
                    isler = plan_df.copy()
                    filter_desc = []

                    if sel_kat != "Tümü":
                        isler = isler[isler['kat_parsed'] == sel_kat]
                        filter_desc.append(f"🏢 {sel_kat}")

                    if sel_bolum != "Tümü":
                        isler = isler[isler['bolum_parsed'] == sel_bolum]
                        filter_desc.append(f"🏭 {sel_bolum}")

                    if sel_hat != "Tümü" and hatlar_unique:
                        isler = isler[isler['hat_parsed'] == sel_hat]
                        filter_desc.append(f"🛤️ {sel_hat}")

                    filter_text = " > ".join(filter_desc) if filter_desc else "🌐 Tüm Lokasyonlar"
                    st.info(f"💡 **{filter_text}** için **{len(isler)}** adet temizlik görevi listelendi.")

                    # YETKİ KONTROLÜ
                    is_controller = (st.session_state.user in CONTROLLER_ROLES) or (st.session_state.user in ADMIN_USERS)
                    if not is_controller:
                        st.warning(f"⚠️ {st.session_state.user}, bu alanda sadece Görüntüleme yetkiniz var.")

                    with st.form("temizlik_kayit_formu"):
                        kayitlar = []
                        h1, h2, h3, h4 = st.columns([3, 2, 2, 2])
                        h1.caption("📍 Ekipman / Alan")
                        h2.caption("🧪 Kimyasal / Sıklık")
                        h3.caption("❓ Durum")
                        h4.caption("🔍 Doğrulama / Not")
                        st.markdown("---")

                        for idx, row in isler.iterrows():
                            r1, r2, r3, r4 = st.columns([3, 2, 2, 2])
                            r1.write(f"**{row['ekipman_alan']}** \n ({row['risk_seviyesi']})")
                            r2.caption(f"{row['kimyasal_adi']} \n {row['siklik']}")

                            with st.expander("ℹ️ Detaylar ve Yöntem"):
                                st.markdown(f"**Yöntem:** {row['metot_detay'] if row['metot_detay'] else 'Standart prosedür.'}")
                                st.info(f"🧬 **Validasyon:** {row['validasyon_siklik']} | **Verifikasyon:** {row['verifikasyon']} ({row['verifikasyon_siklik']})")
                                st.caption(f"**Uygulayıcı:** {row['uygulayici']} | **Kontrol:** {row['kontrol_rol']}")

                            # Durum Girişi
                            durum = r3.selectbox("Seç", ["TAMAMLANDI", "YAPILMADI"], key=f"d_{idx}", label_visibility="collapsed", disabled=not is_controller)

                            val_not = ""
                            if durum == "TAMAMLANDI":
                                if row['verifikasyon'] and row['verifikasyon'] != 'Görsel':
                                    r4.info(f"🧬 {row['verifikasyon']}")
                                    val_not = r4.text_input("Sonuç/Not", placeholder="RLU/Puan...", key=f"v_res_{idx}", disabled=not is_controller)
                                else:
                                    val_not = r4.text_input("Not", key=f"v_note_{idx}", label_visibility="collapsed", disabled=not is_controller)
                            else:
                                val_not = r4.selectbox("Neden?", ["Arıza", "Malzeme Eksik", "Zaman Yetersiz"], key=f"v_why_{idx}", label_visibility="collapsed", disabled=not is_controller)

                            if is_controller:
                                kayitlar.append({
                                    "tarih": str(get_istanbul_time().date()),
                                    "saat": get_istanbul_time().strftime("%H:%M"),
                                    "kullanici": st.session_state.user,
                                    "bolum": row['bolum_parsed'],
                                    "islem": row['ekipman_alan'],
                                    "durum": durum,
                                    "aciklama": val_not
                                })

                        if st.form_submit_button("💾 TÜM KAYITLARI VERİTABANINA İŞLE", use_container_width=True):
                            if kayitlar:
                                try:
                                    pd.DataFrame(kayitlar).to_sql("temizlik_kayitlari", engine, if_exists='append', index=False)
                                    st.success("✅ Kayıtlar başarıyla işlendi!"); time.sleep(1); st.rerun()
                                except Exception as ex:
                                    st.error(f"Veritabanına yazılırken hata: {ex}")
                            else:
                                st.warning("İşlenecek kayıt bulunamadı.")
                else:
                    st.warning("⚠️ Master Plan tanımlanmamış. Lütfen Ayarlar modülünden plan oluşturun.")
            except Exception as e:
                st.error(f"Saha formu yüklenirken hata oluştu: {e}")
                st.caption(f"Detay: {e}")

        with tab_master_plan:
            st.subheader("⚙️ Master Temizlik Planı (Görüntüleme)")
            st.info("💡 Bu ekranda Ayarlar modülünde oluşturulan Master Temizlik Planını görüntüleyebilirsiniz. Değişiklik yapmak için **⚙️ Ayarlar > Temizlik Yönetimi** sayfasını kullanın.")

            try:
                # Ayarlar'daki Master Planı Çek
                master_df = pd.read_sql("SELECT * FROM ayarlar_temizlik_plani", engine)

                if not master_df.empty:
                    # Sütun Sıralaması: ID'yi de gösterelim
                    if 'id' not in master_df.columns:
                        master_df.insert(0, 'id', range(1, len(master_df) + 1))

                    # Görüntüleme için sütun isimlerini düzenle
                    display_columns = {
                        'id': 'Plan ID',
                        'kat': '🏢 Kat',
                        'kat_bolum': '🏭 Bölüm',
                        'yer_ekipman': '⚙️ Ekipman/Alan',
                        'kimyasal': '🧪 Kimyasal',
                        'uygulama_yontemi': '📋 Yöntem',
                        'uygulayici': '👷 Uygulayıcı',
                        'kontrol_eden': '👤 Kontrol',
                        'siklik': '🔄 Sıklık',
                        'validasyon_siklik': '✅ Validasyon',
                        'verifikasyon': '🔬 Verifikasyon Yöntemi',
                        'verifikasyon_siklik': '📅 Verif. Sıklığı',
                        'risk': '⚠️ Risk'
                    }

                    # Sadece mevcut sütunları göster
                    existing_cols = [col for col in display_columns.keys() if col in master_df.columns]
                    display_df = master_df[existing_cols].rename(columns={k: v for k, v in display_columns.items() if k in existing_cols})

                    # READ-ONLY Dataframe (Düzenlenemez)
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        height=600
                    )

                    st.success(f"✅ {len(master_df)} adet temizlik planı kaydı görüntüleniyor.")
                else:
                    st.warning("⚠️ Henüz Master Temizlik Planı tanımlanmamış. Lütfen **⚙️ Ayarlar > Temizlik Yönetimi** sayfasından plan oluşturun.")

            except Exception as e:
                st.error(f"Master plan yüklenirken hata oluştu: {e}")
                st.caption(f"Teknik Detay: {e}")

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
            "📅 Günlük Operasyonel Rapor",
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
                ["🖥️ İnteraktif Görünüm (Ekran)", "📄 Dikey Personel Listesi (PDF)"],
                horizontal=True,
                help="İnteraktif: Ekran üzerinde departman bazlı hiyerarşi | PDF: Dikey hiyerarşik liste"
            )

        if st.button("Raporu Oluştur", use_container_width=True):
            st.markdown(f"### 📋 {rapor_tipi}")

            # 1. ÜRETİM RAPORU
            if rapor_tipi == "🏭 Üretim ve Verimlilik":
                df = run_query(f"SELECT * FROM depo_giris_kayitlari WHERE tarih BETWEEN '{bas_tarih}' AND '{bit_tarih}'")
                if not df.empty:
                    # Sütun isimlerini küçük harfe çevir (güvenlik)
                    df.columns = [c.lower() for c in df.columns]

                    # Özet Kartlar
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Toplam Üretim (Adet)", f"{df['miktar'].sum():,}")
                    k2.metric("Toplam Fire", f"{df['fire'].sum():,}")
                    fire_oran = (df['fire'].sum() / df['miktar'].sum()) * 100 if df['miktar'].sum() > 0 else 0
                    k3.metric("Ortalama Fire Oranı", f"%{fire_oran:.2f}")

                    # Ürün Bazlı Özet Tablo
                    st.subheader("📦 Ürün Bazında Özet")
                    urun_ozet = df.groupby('urun').agg({
                        'miktar': 'sum',
                        'fire': 'sum',
                        'lot_no': 'count'
                    }).reset_index()
                    urun_ozet.columns = ['Ürün Adı', 'Toplam Üretim', 'Toplam Fire', 'Lot Sayısı']
                    urun_ozet['Fire Oranı (%)'] = (urun_ozet['Toplam Fire'] / urun_ozet['Toplam Üretim'] * 100).round(2)
                    urun_ozet = urun_ozet.sort_values('Toplam Üretim', ascending=False)
                    st.dataframe(urun_ozet, use_container_width=True, hide_index=True)

                    # Detaylı Kayıtlar - Sütunları Türkçeleştir
                    st.subheader("📋 Detaylı Kayıtlar")
                    cols_to_show = ['tarih', 'saat', 'vardiya', 'urun', 'lot_no', 'miktar', 'fire', 'kullanici', 'notlar']
                    present_cols = [c for c in cols_to_show if c in df.columns]
                    df_display = df[present_cols].copy()

                    rename_map = {
                        'tarih': 'Tarih',
                        'saat': 'Saat',
                        'vardiya': 'Vardiya',
                        'urun': 'Ürün Adı',
                        'lot_no': 'Lot No',
                        'miktar': 'Miktar',
                        'fire': 'Fire',
                        'kullanici': 'Kaydeden Kullanıcı',
                        'notlar': 'Notlar'
                    }
                    df_display.columns = [rename_map.get(c, c) for c in df_display.columns]
                    st.dataframe(df_display, use_container_width=True, hide_index=True)

                    # Excel İndirme Butonu
                    try:
                        import io
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_display.to_excel(writer, index=False, sheet_name='Detaylı Kayıtlar')
                            urun_ozet.to_excel(writer, index=False, sheet_name='Ürün Özeti')
                        excel_data = output.getvalue()

                        st.download_button(
                            label="📥 Excel Olarak İndir",
                            data=excel_data,
                            file_name=f"uretim_raporu_{bas_tarih}_{bit_tarih}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.caption(f"ℹ️ Excel indirme: openpyxl kütüphanesi gereklidir (pip install openpyxl)")

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

            # 3. GÜNLÜK OPERASYONEL RAPOR (YENİ)
            elif rapor_tipi == "📅 Günlük Operasyonel Rapor":
                st.info("💡 Bu rapor belirlediğiniz tarihteki tüm işlemleri, devamsızlıkları ve performans metriklerini özetler.")

                # Yardımcı fonksiyonlar (30 satır kuralına uygun)
                def _cek_kpi_verileri(t):
                    return run_query(f"SELECT tarih, saat, urun, karar, notlar, vardiya FROM urun_kpi_kontrol WHERE tarih='{t}'")

                def _cek_uretim_verileri(t):
                    return run_query(f"SELECT tarih, saat, urun, miktar, vardiya FROM depo_giris_kayitlari WHERE tarih='{t}'")

                def _cek_hijyen_verileri(t):
                    return run_query(f"SELECT tarih, saat, personel, durum, sebep, aksiyon, vardiya, bolum FROM hijyen_kontrol_kayitlari WHERE tarih='{t}'")

                def _cek_temizlik_verileri(t):
                    return run_query(f"SELECT tarih, saat, bolum, islem, durum FROM temizlik_kayitlari WHERE tarih='{t}'")

                # Verileri Çek
                t_str = str(bas_tarih)
                kpi_df = _cek_kpi_verileri(t_str)
                uretim_df = _cek_uretim_verileri(t_str)
                hijyen_df = _cek_hijyen_verileri(t_str)
                temizlik_df = _cek_temizlik_verileri(t_str)

                # EK FİLTRE PANELİ (Sadece bu rapor için)
                st.write("---")
                f1, f2 = st.columns(2)
                v_secim = f1.multiselect("Vardiya Seçimi", VARDIYA_LISTESI, default=VARDIYA_LISTESI)

                # Departman listesini al
                depts = hijyen_df['bolum'].dropna().unique().tolist() if not hijyen_df.empty else []
                d_secim = f2.multiselect("Departman Seçimi", ["Tümü"] + depts, default=["Tümü"])

                # Filtreleri Uygula
                if not kpi_df.empty:
                    kpi_df = kpi_df[kpi_df['vardiya'].isin(v_secim)] if 'vardiya' in kpi_df.columns else kpi_df
                if not uretim_df.empty:
                    uretim_df = uretim_df[uretim_df['vardiya'].isin(v_secim)]
                if not hijyen_df.empty:
                    hijyen_df = hijyen_df[hijyen_df['vardiya'].isin(v_secim)]
                    if "Tümü" not in d_secim:
                        hijyen_df = hijyen_df[hijyen_df['bolum'].isin(d_secim)]

                # GPM - Mock Data
                gpm_mock = pd.DataFrame([
                    {"Metrik": "OEE", "Hedef": "%85", "Gerceklesen": "%78", "Sapma": "-7pp", "Durum": "🔴"},
                    {"Metrik": "Fire Oranı", "Hedef": "<%3", "Gerceklesen": "%2.1", "Sapma": "+0.9pp", "Durum": "🟢"},
                    {"Metrik": "Verimlilik", "Hedef": "%90", "Gerceklesen": "%91", "Sapma": "+1pp", "Durum": "🟢"}
                ])

                # BÖLÜM 0 — YÖNETİCİ ÖZET BANNER'I
                red_sayisi = len(kpi_df[kpi_df['karar'] == 'RED']) if not kpi_df.empty else 0
                uygunsuz_hijyen = len(hijyen_df[hijyen_df['durum'] != 'Sorun Yok']) if not hijyen_df.empty else 0
                mazeretsiz = len(hijyen_df[hijyen_df['durum'] == 'Gelmedi']) if not hijyen_df.empty else 0

                toplam_hata = red_sayisi + uygunsuz_hijyen + mazeretsiz
                if toplam_hata > 0:
                    st.error(f"🔴 DİKKAT GEREKTİREN DURUMLAR VAR  \n→ {red_sayisi} RED karar | {mazeretsiz} Mazeretsiz Devamsızlık | {uygunsuz_hijyen} Hijyen Uygunsuzluğu")
                else:
                    st.success("🟢 NORMAL — Tüm sistemler standart dahilinde çalışıyor")

                # BÖLÜM 1 — METRİK KART SATIRLARI
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("KPI Analiz", len(kpi_df))
                m2.metric("ONAY", len(kpi_df[kpi_df['karar']=='ONAY']) if not kpi_df.empty else 0)
                m3.metric("RED", red_sayisi)
                m4.metric("Üretim Kaydı", len(uretim_df))
                m5.metric("GPM Sapma", "-7pp", delta="-7%", delta_color="inverse")

                h1, h2, h3, h4, h5 = st.columns(5)
                toplam_varsayilan = 100 # Örnek personel sayısı
                h1.metric("Topl. Pers.", toplam_varsayilan)
                h2.metric("Gelen", toplam_varsayilan - mazeretsiz)
                h3.metric("Gelmeyen", mazeretsiz, delta=f"{mazeretsiz}", delta_color="inverse")
                h4.metric("Hijyen Kont.", len(hijyen_df))
                h5.metric("Uygunsuz", uygunsuz_hijyen)

                # BÖLÜM 2 — PERSONEL DEVAMSIZLIK PANELİ
                with st.expander(f"👥 Personel Devamsızlık Durumu ({mazeretsiz} kişi)"):
                    st.progress((toplam_varsayilan - mazeretsiz) / toplam_varsayilan)

                    # Departman bazlı özet
                    if not hijyen_df.empty:
                        dept_ozet = hijyen_df.groupby('bolum').size().reset_index(name='Gelmeyen')
                        for _, row in dept_ozet.iterrows():
                            if row['bolum'] == 'Üretim' and row['Gelmeyen'] > 2:
                                st.warning(f"⚠️ ÜRETİM departmanı bugün kritik eksik kapasitede ({row['Gelmeyen']} kişi gelmedi)")
                            elif row['Gelmeyen'] > 0:
                                st.info(f"📍 {row['bolum']} departmanında {row['Gelmeyen']} kişi bulunmamaktadır.")

                    if mazeretsiz > 0:
                        dev_df = hijyen_df[hijyen_df['durum'] == 'Gelmedi'].copy()
                        dev_df['İşlem'] = "🔴"
                        st.dataframe(dev_df[['personel', 'bolum', 'durum', 'sebep', 'İşlem']], use_container_width=True, hide_index=True)
                    else:
                        st.success("Tüm personel katılım sağladı.")

                # BÖLÜM 3 — PERSONEL HİJYEN KONTROL PANELİ
                with st.expander(f"🧼 Personel Hijyen Kontrolleri ({len(hijyen_df)} kontrol)"):
                    if not hijyen_df.empty:
                        uyg_df = hijyen_df[hijyen_df['durum'] != 'Sorun Yok']
                        if not uyg_df.empty:
                            st.warning(f"{len(uyg_df)} personelde hijyen uygunsuzluğu tespit edildi.")
                            st.dataframe(uyg_df, use_container_width=True)
                        else: st.success("Tüm hijyen kontrolleri uygun.")

                # BÖLÜM 4 — GPM SONUÇLARI PANELİ
                with st.expander("📈 GPM — Günlük Performans Metrikleri"):
                    st.table(gpm_mock)

                # BÖLÜM 5 — KRONOLOJİK İŞLEM AKIŞI
                st.subheader("🕔 Kronolojik İşlem Akışı")
                flow_data = []
                if not kpi_df.empty:
                    for _, r in kpi_df.iterrows():
                        flow_data.append({"Saat": r['saat'], "Modül": "🍩 KPI", "Özet": f"{r['urun']} - {r['karar']}", "Durum": "🟢" if r['karar']=='ONAY' else "🔴"})
                if not uretim_df.empty:
                    for _, r in uretim_df.iterrows():
                        flow_data.append({"Saat": r['saat'], "Modül": "🏭 Üretim", "Özet": f"{r['urun']} ({r['miktar']} adet)", "Durum": "🟢"})
                if not hijyen_df.empty:
                    for _, r in hijyen_df.iterrows():
                        status = "🔴" if r['durum'] != 'Sorun Yok' else "🟢"
                        flow_data.append({"Saat": r['saat'], "Modül": "🧼 Hijyen", "Özet": f"{r['personel']} - {r['durum']}", "Durum": status})

                if flow_data:
                    flow_df = pd.DataFrame(flow_data).sort_values("Saat")
                    st.dataframe(flow_df, use_container_width=True, hide_index=True)
                else: st.info("Bu tarihte herhangi bir işlem kaydı bulunamadı.")

                # BÖLÜM 6 — MODÜL DETAY EXPANDERLERİ
                st.subheader("🔍 Modül Detayları")
                with st.expander("🍩 KPI Kontrol Kayıtları"):
                    if not kpi_df.empty:
                        st.dataframe(kpi_df, use_container_width=True)
                    else:
                        st.info("Kayıt yok")

                with st.expander("🏭 Üretim Kayıtları"):
                    if not uretim_df.empty:
                        st.dataframe(uretim_df, use_container_width=True)
                    else:
                        st.info("Kayıt yok")

                with st.expander("👥 Devamsızlık Detayı"):
                    if not hijyen_df.empty:
                        dev_detay = hijyen_df[hijyen_df['durum'] == 'Gelmedi']
                        if not dev_detay.empty:
                            st.dataframe(dev_detay, use_container_width=True)
                        else:
                            st.info("Devamsızlık yok")

                with st.expander("🧼 Hijyen Kontrol Detayı"):
                    if not hijyen_df.empty:
                        st.dataframe(hijyen_df, use_container_width=True)
                    else:
                        st.info("Kayıt yok")

                with st.expander("🧹 Temizlik Detayı"):
                    if not temizlik_df.empty:
                        st.dataframe(temizlik_df, use_container_width=True)
                    else:
                        st.info("Kayıt yok")

                with st.expander("⚠️ Tüm RED/Uygunsuz Kararlar"):
                    negatif_data = []
                    if not kpi_df.empty:
                        for _, r in kpi_df[kpi_df['karar'] == 'RED'].iterrows():
                            negatif_data.append({"Tip": "KPI RED", "Detay": f"{r['urun']} - {r['notlar']}"})
                    if not hijyen_df.empty:
                        for _, r in hijyen_df[hijyen_df['durum'] != 'Sorun Yok'].iterrows():
                            negatif_data.append({"Tip": "Hijyen Uygunsuzluk", "Detay": f"{r['personel']} - {r['durum']} ({r['sebep']})"})

                    if negatif_data:
                        st.dataframe(pd.DataFrame(negatif_data), use_container_width=True)
                    else: st.success("Herhangi bir uygunsuzluk bulunamadı.")

                # BÖLÜM 7 — OTOMATİK GÜNLÜK ÖZET METNİ
                st.divider()
                durum_msg = "Tüm sistemler normal seyretti." if toplam_hata == 0 else "Yukarıdaki kalemler yönetici onayı gerektirmektedir."
                st.info(f"""
                **📝 Günlük Rapor Özeti**
                {t_str} tarihinde toplam {len(flow_data)} işlem kaydedildi.
                Kalite analizlerinde {len(kpi_df[kpi_df['karar']=='ONAY']) if not kpi_df.empty else 0} ONAY, {red_sayisi} RED karar verildi.
                Personel devamsızlığı: {mazeretsiz} kişi.
                Hijyen kontrollerinde {uygunsuz_hijyen} uygunsuzluk tespit edildi.
                GPM metriklerinden 1 tanesi hedefin altında kaldı.
                **{durum_msg}**
                """)

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

                    # Yöneticiler (Seviye 2-5: Direktör, Müdür, Koordinatör, Şef)
                    for seviye in [2, 3, 4, 5]:
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

                    # Personel (Seviye 6+)
                    personel_staff = staff_df[staff_df['pozisyon_seviye'] > 5]
                    if not personel_staff.empty:
                        st.markdown(f"*{get_position_icon(6)} Personel* ({len(personel_staff)} kişi)")
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
                        # Gelişmiş İstatistik (Toplam Tree Bazlı)
                        all_sub_ids = get_all_sub_department_ids(dept_id)
                        # Bu bölüm ve alt bölümlerdeki toplam personel
                        tree_staff = pers_df[pers_df['departman_id'].isin(all_sub_ids)]

                        tree_mgr_count = len(tree_staff[(tree_staff['pozisyon_seviye'] >= 2) & (tree_staff['pozisyon_seviye'] <= 5)])
                        tree_staff_count = len(tree_staff[tree_staff['pozisyon_seviye'] > 5])
                        # total_count değişkeni zaten recursive hesaplanmıştı ama buradan da teyit edebiliriz
                        tree_total = len(tree_staff[tree_staff['pozisyon_seviye'] >= 2]) # Seviye 1 hariç

                        # Departman başlığı
                        indent = "  " * level
                        icon = "🏢" if level == 0 else "📍"

                        header_text = f"{icon} **{dept_name}** | Toplam: **{tree_total}** (👔 {tree_mgr_count} Yönetici, 👥 {tree_staff_count} Personel)"

                        with st.expander(header_text, expanded=is_expanded):
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
                                    manager_count = len(sub_staff[sub_staff['pozisyon_seviye'] <= 5])
                                    staff_count = len(sub_staff[sub_staff['pozisyon_seviye'] > 5])

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

                def generate_dept_rows_recursive(dept_id, dept_name, all_depts, pers_df, level=0):
                    """Liste görünümü için recursive TABLO SATIRLARI (TR) oluşturur"""
                    html = ""

                    # Bu departmandaki personel
                    dept_staff = get_dept_staff(dept_id, pers_df)

                    # Alt departmanlar
                    sub_depts = get_sub_departments(dept_id, all_depts)

                    # Toplam personel sayısı (recursive)
                    total_count = count_total_staff_recursive(dept_id, all_depts, pers_df)

                    if total_count > 0:
                        # 1. DEPARTMAN BAŞLIĞI (Tablo Satırı)
                        # Seviye 0 (Direktörlükler/Ana Bölümler) ise vurgulu başlık
                        if level == 0:
                             html += f'<tr class="level-0-row"><td colspan="3">🏢 {dept_name.upper()} ({total_count} kişi)</td></tr>'
                        else:
                             # Alt bölümler için girintili başlık (Sadece 1. kolona yaz, diğerleri boş)
                             indent_style = f"padding-left: {20 + (level * 20)}px !important;"
                             html += f'<tr><td style="{indent_style} font-weight:bold; color:#555;">📍 {dept_name} <span style="font-size:11px; font-weight:normal;">({total_count} kişi)</span></td><td></td><td></td></tr>'

                        # 2. PERSONEL LİSTESİ
                        if not dept_staff.empty:
                            staff_sorted = dept_staff.sort_values('pozisyon_seviye')

                            for _, person in staff_sorted.iterrows():
                                # GÖREV / ROL GÖRÜNTÜLEME MANTIĞI (Gelişmiş)
                                raw_gorev = person['gorev']
                                raw_rol = person['rol']

                                # Eğer görev sütunu dolu ve boşluk değilse onu kullan, yoksa ROL'ü kullan
                                if pd.notna(raw_gorev) and str(raw_gorev).strip() != "":
                                    gorev = str(raw_gorev).strip()
                                else:
                                    gorev = str(raw_rol).strip() if pd.notna(raw_rol) else ""
                                p_seviye = int(person['pozisyon_seviye'])

                                # Stil Belirleme
                                row_class = ""
                                name_style = ""
                                role_badge = ""

                                # Yönetici ise (Seviye 2-4)
                                if p_seviye <= 4:
                                    name_style = "font-weight:bold;"
                                    if p_seviye == 2: role_badge = '<span class="role-badge" style="background:#D6EAF8; color:#2874A6;">Direktör</span>'
                                    elif p_seviye == 3: role_badge = '<span class="role-badge" style="background:#EBF5FB; color:#2E86C1;">Müdür</span>'
                                    elif p_seviye == 4: role_badge = '<span class="role-badge">Yönetici</span>'

                                # Hiyerarşik Girinti (Seviyeye göre)
                                # Temel girinti (Departman level'ı) + Personel seviyesi farkı
                                base_indent = 20 + (level * 20)
                                if p_seviye > 2: base_indent += 15

                                indent_css = f"padding-left: {base_indent}px !important;"
                                icon = get_position_icon(p_seviye)

                                html += f'''
                                <tr>
                                    <td style="{indent_css} color:#2C3E50;">{icon} {get_position_name(p_seviye)}</td>
                                    <td style="{name_style}">{person["ad_soyad"]}</td>
                                    <td>{role_badge} {gorev}</td>
                                </tr>
                                '''

                        # 3. ALT DEPARTMANLAR (Recursive)
                        for _, sub in sub_depts.iterrows():
                            html += generate_dept_rows_recursive(sub['id'], sub['bolum_adi'], all_depts, pers_df, level + 1)

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

                        # [DEBUG] HAKAN ÖZALP KONTROL BLOĞU (Scope Düzeltmesi)
                        # Canlı veride Hakan Özalp'in tam olarak nasıl göründüğünü denetler.
                        hakan_check = pers_df[pers_df['ad_soyad'].astype(str).str.contains("Hakan Özalp", case=False, na=False)]
                        if not hakan_check.empty:
                            with st.expander("🛠️ TEKNİK DÜZELTME BİLGİSİ: Hakan Özalp Verisi", expanded=True):
                                st.info("Aşağıdaki veri doğrudan veritabanından okunmaktadır:")
                                st.dataframe(hakan_check[['id', 'ad_soyad', 'pozisyon_seviye', 'gorev', 'rol', 'departman_adi']])
                                h_seviye = hakan_check.iloc[0]['pozisyon_seviye']
                                if h_seviye <= 4:
                                    st.success(f"✅ Sistem Hakan Bey'i YÖNETİCİ (Seviye {h_seviye}) olarak görüyor.")
                                else:
                                    st.error(f"❌ Sistem Hakan Bey'i PERSONEL (Seviye {h_seviye}) olarak görüyor. Lütfen Personel Listesi'nden 'Seviye' ayarını kontrol edin.")

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
                        # ═══════════════════════════════════════════════════════════
                        # 📄 DİKEY PERSONEL LİSTESİ (PDF)
                        # ═══════════════════════════════════════════════════════════
                        elif gorunum_tipi == "📄 Dikey Personel Listesi (PDF)":
                            st.info("📂 Dikey hiyerarşik liste - Personel organizasyon yapısı")

                            # Hiyerarşik TABLO satırlarını oluştur
                            table_rows = ""

                            # 1. Üst Yönetim (Seviye 0-1)
                            ust_yonetim = pers_df[pers_df['pozisyon_seviye'] <= 1].sort_values('pozisyon_seviye')
                            if not ust_yonetim.empty:
                                table_rows += '<tr class="level-0-row"><td colspan="3">🏛️ ÜST YÖNETİM</td></tr>'
                                for _, person in ust_yonetim.iterrows():
                                    raw_gorev = person['gorev']
                                    raw_rol = person['rol']
                                    gorev = str(raw_gorev).strip() if pd.notna(raw_gorev) and str(raw_gorev).strip() != "" else str(raw_rol).strip()

                                    icon = "👑" if person['pozisyon_seviye'] == 1 else "🏛️"
                                    table_rows += f'''
                                    <tr>
                                        <td class="level-1" style="font-weight:bold;">{icon} {get_position_name(person['pozisyon_seviye'])}</td>
                                        <td style="font-weight:bold;">{person["ad_soyad"]}</td>
                                        <td><span class="role-badge" style="background:#F9E79F; color:#D35400;">Yönetim</span> {gorev}</td>
                                    </tr>
                                    '''

                            # 2. Departman Bazlı Hiyerarşi (Recursive)
                            all_depts = get_all_departments()
                            top_level_depts = all_depts[
                                (all_depts['ana_departman_id'].isna()) |
                                (all_depts['ana_departman_id'] == 1)
                            ]

                            for _, dept in top_level_depts.iterrows():
                                if dept['id'] != 1: # YÖNETİM hariç
                                    table_rows += generate_dept_rows_recursive(dept['id'], dept['bolum_adi'], all_depts, pers_df)

                            # 3. YAZDIRILABİLİR HTML OLUŞTURMA (MODERN A4 DİKEY)
                            full_html = f"""
                            <!DOCTYPE html>
                            <html lang="tr">
                            <head>
                                <meta charset="utf-8">
                                <title>Ekleristan Organizasyon Listesi</title>
                                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
                                <style>
                                    :root {{
                                        --primary: #1a2a6c;
                                        --secondary: #2C3E50;
                                        --bg: #f8f9fa;
                                        --text: #333;
                                        --border: #eef1f5;
                                    }}

                                    @media print {{
                                        @page {{ size: A4 portrait; margin: 15mm; }}
                                        body {{ background: transparent !important; padding: 0 !important; }}
                                        .page-container {{ border: none !important; box-shadow: none !important; width: 100% !important; margin: 0 !important; padding: 0 !important; }}
                                    }}

                                    body {{
                                        font-family: 'Inter', sans-serif;
                                        background-color: #f0f2f6;
                                        color: var(--text);
                                        margin: 0;
                                        padding: 40px 0;
                                        display: flex;
                                        justify-content: center;
                                    }}

                                    /* Real A4 Paper Look */
                                    .page-container {{
                                        background: white;
                                        width: 210mm;
                                        min-height: 297mm;
                                        padding: 20mm;
                                        box-sizing: border-box;
                                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                                        border-radius: 4px;
                                        position: relative;
                                    }}

                                    .header {{
                                        text-align: center;
                                        border-bottom: 2px solid var(--primary);
                                        margin-bottom: 30px;
                                        padding-bottom: 15px;
                                    }}

                                    h2 {{
                                        color: var(--primary);
                                        margin: 0;
                                        font-weight: 700;
                                        letter-spacing: -0.5px;
                                        font-size: 24px;
                                    }}

                                    .meta {{
                                        color: #888;
                                        font-size: 11px;
                                        margin-top: 8px;
                                        text-transform: uppercase;
                                        letter-spacing: 1px;
                                    }}

                                    table {{
                                        width: 100%;
                                        border-collapse: collapse;
                                        margin-top: 5px;
                                    }}

                                    th {{
                                        background: var(--primary);
                                        color: white;
                                        text-align: left;
                                        padding: 12px 15px;
                                        font-size: 12px;
                                        font-weight: 600;
                                        text-transform: uppercase;
                                    }}

                                    td {{
                                        padding: 10px 15px;
                                        border-bottom: 1px solid var(--border);
                                        font-size: 13px;
                                        vertical-align: middle;
                                    }}

                                    /* Hiyerarşi Stilleri */
                                    .level-0-row td {{
                                        background-color: #f4f7f9 !important;
                                        color: var(--primary) !important;
                                        font-weight: 700 !important;
                                        font-size: 15px !important;
                                        border-top: 2px solid var(--primary) !important;
                                        padding: 15px !important;
                                    }}

                                    .sub-dept-row td {{
                                        background-color: #fafbfc;
                                        font-weight: 600;
                                        color: #555;
                                        padding-top: 12px;
                                        padding-bottom: 12px;
                                    }}

                                    tr:hover {{ background-color: #fdfdfd; }}

                                    .role-badge {{
                                        display: inline-block;
                                        background: #eef2f7;
                                        padding: 3px 8px;
                                        border-radius: 4px;
                                        font-size: 10px;
                                        color: #5d6d7e;
                                        font-weight: 600;
                                        border: 1px solid #d5dbe5;
                                        margin-right: 6px;
                                    }}

                                    .manager-name {{ font-weight: 700; color: #111; }}
                                    .staff-name {{ font-weight: 400; color: #333; }}

                                    .footer-note {{
                                        position: absolute;
                                        bottom: 15mm;
                                        left: 20mm;
                                        right: 20mm;
                                        text-align: center;
                                        font-size: 10px;
                                        color: #aaa;
                                        border-top: 1px solid #eee;
                                        padding-top: 10px;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="page-container">
                                    <div class="header">
                                        <h2>EKLERİSTAN GIDA</h2>
                                        <h2>KURUMSAL ORGANİZASYON LİSTESİ</h2>
                                        <div class="meta">RAPOR TARİHİ: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
                                    </div>

                                    <table>
                                        <thead>
                                            <tr>
                                                <th style="width: 40%;">Departman / Birim / Pozisyon</th>
                                                <th style="width: 30%;">Ad Soyad</th>
                                                <th style="width: 30%;">Görev Tanımı</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {table_rows}
                                        </tbody>
                                    </table>

                                    <div class="footer-note">
                                        Bu döküman Ekleristan QMS sistemi tarafından otomatik olarak oluşturulmuştur.
                                    </div>
                                </div>
                            </body>
                            </html>
                            """

                            # Ekranda göster ve indir
                            st.components.v1.html(full_html, height=1000, scrolling=True)

                            c1, c2 = st.columns([1, 1])
                            with c1:
                                st.download_button(
                                    label="📥 Listeyi İndir (HTML/PDF)",
                                    data=full_html,
                                    file_name=f"Ekleristan_Organizasyon_Listesi_{datetime.now().strftime('%d_%m_%Y')}.html",
                                    mime="text/html",
                                    key="btn_download_org_list_modern",
                                    use_container_width=True
                                )
                            with c2:
                                if st.button("🖨️ Yazdır (PDF Olarak Kaydet)", use_container_width=True):
                                    st.info("💡 Dosyayı indirdikten sonra açın ve CTRL+P tuşlarına basarak 'PDF Olarak Kaydet' deyin.")




                except Exception as e:
                    st.error(f"Organizasyon şeması oluşturulurken hata: {e}")
                    st.info("💡 Eğer migration script'i henüz çalıştırmadıysanız, lütfen önce `sql/supabase_personel_org_restructure.sql` dosyasını Supabase SQL Editor'de çalıştırın.")


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

        st.title("⚙️ Sistem Ayarları ve Personel Yönetimi")

        with st.sidebar:
            st.header("⚙️ Genel Ayarlar")

            # Cache Temizleme Butonu (Acil Durumlar İçin)
            if st.button("🧹 Önbelleği Temizle (Veri Güncelle)", use_container_width=True):
                st.cache_data.clear()
                st.toast("Önbellek temizlendi! Sayfa yenileniyor...", icon="🔄")
                time.sleep(1)
                st.rerun()

            selected_modul = st.selectbox(
                "Modül Seçiniz",
                ["Personel Yönetimi", "Vardiya Programı", "Bölüm Ayarları", "Yetkilendirme", "Sistem Bilgisi"]
            )

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
            # Alt sekmeler: Form ve Tablo
            # --- UI FIX: Persistent Tab Selection (st.tabs resets on rerun, st.radio with key remembers) ---
            # Define Tabs
            p_tabs = ["📅 Vardiya Çalışma Programı", "📝 Personel Ekle/Düzenle", "📋 Tüm Personel Listesi"]

            # Initialize Session State for this tab if not exists
            if "nav_personel" not in st.session_state:
                st.session_state["nav_personel"] = p_tabs[0]

            # Render Radio as Tabs (Horizontal)
            # Use 'label_visibility="collapsed"' to hide the label "Sekme"
            st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
            p_selected_tab = st.radio(
                "Personel Sekmesi",
                p_tabs,
                index=0,
                key="nav_personel",
                horizontal=True,
                label_visibility="collapsed"
            )
            st.markdown("---")

            # --- ERKEN YÜKLEME: LİSTELERİ HAZIRLA (Tüm sekmeler için gerekli) ---
            try:
                # YENİ: Hiyerarşik Yapı
                dept_options = get_department_options_hierarchical()
            except:
                dept_options = {0: "- Seçiniz -"}

            try:
                yon_df = pd.read_sql("SELECT id, ad_soyad FROM personel WHERE ad_soyad IS NOT NULL AND pozisyon_seviye <= 5 ORDER BY ad_soyad", engine)
                yonetici_options = {0: "- Yok -"}
                for _, row in yon_df.iterrows():
                    yonetici_options[row['id']] = row['ad_soyad']
            except:
                yonetici_options = {0: "- Yok -"}

            # >>> YENİ SEKME: VARDIYA ÇALIŞMA PROGRAMI (TOPLU GİRİŞ VERSİYONU) <<<
            # >>> YENİ SEKME: VARDIYA ÇALIŞMA PROGRAMI (TOPLU GİRİŞ VERSİYONU) <<<
            if p_selected_tab == p_tabs[0]:
                st.subheader("📅 Dönemsel Vardiya Planlama (Toplu Giriş)")
                st.caption("Bölüm seçerek o bölümdeki tüm personellerin vardiya ve izinlerini tek seferde planlayabilirsiniz.")

                # ADIM 1: FİLTRELEME & HAZIRLIK
                with st.container():
                    c1, c2, c3 = st.columns([2, 1, 1])

                    # Bölüm Seçimi
                    secilen_bolum_id = c1.selectbox(
                        "📍 Bölüm Seçimi (Listelemek için zorunludur)",
                        options=list(dept_options.keys()),
                        format_func=lambda x: dept_options[x],
                        index=0
                    )

                    # Tarih Aralığı
                    today = datetime.now()
                    next_monday = today + timedelta(days=(7 - today.weekday()))
                    next_sunday = next_monday + timedelta(days=6)

                    p_start = c2.date_input("Bağlangıç Tarihi", value=next_monday)
                    p_end = c3.date_input("Bitiş Tarihi", value=next_sunday)

                st.divider()

                # ADIM 2: TOPLU LİSTE EDİTÖRÜ
                if secilen_bolum_id != 0:
                    try:
                        # Hiyerarşik olarak alt departmanları da kapsa
                        target_dept_ids = get_all_sub_department_ids(secilen_bolum_id)

                        if len(target_dept_ids) == 1:
                            t_sql = text("SELECT id, ad_soyad, gorev FROM personel WHERE durum = 'AKTİF' AND departman_id = :d ORDER BY ad_soyad")
                            params = {"d": target_dept_ids[0]}
                        else:
                            # Liste olarak ver
                            ids_tuple = tuple(target_dept_ids)
                            t_sql = text(f"SELECT id, ad_soyad, gorev FROM personel WHERE durum = 'AKTİF' AND departman_id IN {ids_tuple} ORDER BY ad_soyad")
                            params = {}

                        with engine.connect() as conn:
                            pers_data = pd.read_sql(t_sql, conn, params=params)


                        if not pers_data.empty:
                            # Düzenlenebilir DataFrame Hazırla
                            # Önce MEVCUT programı çek (Varsa üzerine yazmak için)
                            # Bu tarih aralığında bu personellerin kaydı var mı?
                            sch_sql = text("""
                                SELECT personel_id, vardiya, izin_gunleri, aciklama
                                FROM personel_vardiya_programi
                                WHERE baslangic_tarihi = :s AND bitis_tarihi = :e
                                AND personel_id IN :p_ids
                            """)

                            # Personel ID listesi
                            p_ids_list = pers_data['id'].tolist()
                            if not p_ids_list:
                                p_ids_list = [0] # Empty check

                            with engine.connect() as conn:
                                # Tuple sorunu için dinamik text
                                s_sql = text(f"SELECT personel_id, vardiya, izin_gunleri, aciklama FROM personel_vardiya_programi WHERE baslangic_tarihi = '{p_start}' AND bitis_tarihi = '{p_end}'")
                                existing_sch = pd.read_sql(s_sql, conn)

                            # Merge (Left Join)
                            merged_df = pd.merge(pers_data, existing_sch, left_on='id', right_on='personel_id', how='left')

                            edit_df = merged_df.copy()
                            # Vardiya varsa kullan, yoksa Gündüz
                            edit_df['vardiya'] = edit_df['vardiya'].fillna("GÜNDÜZ VARDİYASI")
                            # İzin varsa kullan, yoksa boş string (SelectboxColumn string bekler)
                            edit_df['izin_gunleri'] = edit_df['izin_gunleri'].fillna("")
                            edit_df['aciklama'] = edit_df['aciklama'].fillna("")
                            # Seçim kutusu - Varsayılan False olsun ki yanlışlıkla ezilmesin, ya da True?
                            # Kullanıcı "Girdiğim veriler siliniyor" dediği için, mevcut veriyi görüp düzeltebilmeli.
                            # Hepsini True yaparsak, hepsini tekrar kaydeder.
                            edit_df['secim'] = True

                            st.info(f"📋 **{dept_options[secilen_bolum_id]}** bölümünde (ve alt birimlerinde) {len(edit_df)} personel listeleniyor. Mevcut kayıtlar otomatik yüklenmiştir.")

                            edited_schedule = st.data_editor(
                                edit_df,
                                use_container_width=True,
                                hide_index=True,
                                num_rows="fixed",
                                key=f"shed_editor_{secilen_bolum_id}_{p_start}",
                                column_config={
                                    "id": None,
                                    "personel_id": None,
                                    "secim": st.column_config.CheckboxColumn("Kaydet", width="small", default=True),
                                    "ad_soyad": st.column_config.TextColumn("Personel", width="medium", disabled=True),
                                    "gorev": st.column_config.TextColumn("Görev", width="small", disabled=True),
                                    "vardiya": st.column_config.SelectboxColumn(
                                        "Vardiya",
                                        options=["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"],
                                        width="medium",
                                        required=True
                                    ),
                                    "izin_gunleri": st.column_config.SelectboxColumn(
                                        "Haftalık İzin",
                                        options=[
                                            "Pazar", "Cumartesi,Pazar", "Cumartesi", "Pazartesi",
                                            "Salı", "Çarşamba", "Perşembe", "Cuma"
                                        ],
                                        width="medium",
                                        help="Haftalık izin günü"
                                    ),
                                    "aciklama": st.column_config.TextColumn("Açıklama", width="large")
                                }
                            )

                            # KAYDET BUTONU
                            col_submit, col_info = st.columns([1, 4])
                            if col_submit.button("💾 Seçilenleri Kaydet/Güncelle", type="primary"):
                                if p_end < p_start:
                                    st.error("⚠️ Bitiş tarihi başlangıç tarihinden önce olamaz.")
                                else:
                                    count = 0
                                    try:
                                        with engine.connect() as conn:
                                            # Sadece 'secim' kutusu işaretli olanları kaydet
                                            for index, row in edited_schedule.iterrows():
                                                if row['secim']:
                                                    pid = row['id']
                                                    v = row['vardiya']
                                                    # İzin günleri SelectboxColumn listeden string e döner mi? List dönerse join yap
                                                    # st.data_editor davranışına göre: SelectboxColumn (tek seçim) string döner.
                                                    # Ama önceki kodda MultiselectColumn vardı, şimdi SelectboxColumn yaptık.
                                                    # Kullanıcı "Cumartesi,Pazar" stringini seçecek.
                                                    i = row['izin_gunleri']
                                                    # Eğer liste gelirse stringe çevir (Eski koddan kalıntı koruması)
                                                    if isinstance(i, list):
                                                        i = ",".join(i)
                                                    if i is None: i = ""

                                                    note = row['aciklama']

                                                    # ÖNCE VARSA SİL (Overwrite)
                                                    del_sql = text("DELETE FROM personel_vardiya_programi WHERE personel_id=:p AND baslangic_tarihi=:s AND bitis_tarihi=:e")
                                                    conn.execute(del_sql, {"p": pid, "s": p_start, "e": p_end})

                                                    # SONRA EKLE
                                                    ins_sql = text("""
                                                        INSERT INTO personel_vardiya_programi
                                                        (personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri, aciklama)
                                                        VALUES (:p, :s, :e, :v, :i, :n)
                                                    """)
                                                    conn.execute(ins_sql, {
                                                        "p": pid, "s": p_start, "e": p_end,
                                                        "v": v, "i": i, "n": note
                                                    })
                                                    count += 1
                                            conn.commit()

                                        if count > 0:
                                            st.success(f"✅ {count} personel programı güncellendi!")
                                            time.sleep(1.5); st.rerun()
                                        else:
                                            st.warning("⚠️ Hiçbir personel seçilmedi.")

                                    except Exception as e:
                                        st.error(f"Kayıt Hatası: {e}")

                        else:
                            st.warning("⚠️ Bu bölümde aktif personel bulunamadı.")

                    except Exception as e:
                        st.error(f"Veri çekme hatası: {e}")
                else:
                    st.info("👈 Lütfen işlem yapmak istediğiniz bölümü seçin.")

                st.divider()

                # --- MEVCUT PROGRAM LİSTESİ ---
                with st.container():
                    st.markdown("#### 📋 Program Listesi")

                    # Filtreler
                    col_f1, col_f2 = st.columns(2)
                    show_history = col_f1.checkbox("📜 Geçmiş Kayıtları Göster", value=False)
                    list_dept_filter = col_f2.selectbox(
                        "Departman Filtresi",
                        options=list(dept_options.keys()),
                        format_func=lambda x: dept_options[x],
                        key="sched_list_dept_filter"
                    )

                    try:
                        base_sql = """
                            SELECT
                                p.ad_soyad,
                                d.bolum_adi,
                                v.baslangic_tarihi,
                                v.bitis_tarihi,
                                v.vardiya,
                                v.izin_gunleri,
                                v.aciklama,
                                v.id
                            FROM personel_vardiya_programi v
                            JOIN personel p ON v.personel_id = p.id
                            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
                        """

                        conditions = []
                        if not show_history:
                            conditions.append("v.bitis_tarihi >= CURRENT_DATE")

                        if list_dept_filter != 0:
                            conditions.append(f"p.departman_id = {list_dept_filter}")

                        if conditions:
                            base_sql += " WHERE " + " AND ".join(conditions)

                        base_sql += " ORDER BY v.baslangic_tarihi DESC, p.ad_soyad"

                        prog_df = pd.read_sql(base_sql, engine)

                        if not prog_df.empty:
                            st.dataframe(
                                prog_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "ad_soyad": "Personel",
                                    "bolum_adi": "Bölüm",
                                    "baslangic_tarihi": "Başlangıç",
                                    "bitis_tarihi": "Bitiş",
                                    "vardiya": "Vardiya",
                                    "izin_gunleri": "İzin Günleri",
                                    "aciklama": "Not",
                                    "id": None
                                }
                            )

                            # Silme İşlemi (Opsiyonel)
                            with st.expander("🗑️ Program Sil"):
                                del_id = st.number_input("Silinecek Program ID", min_value=1, step=1)
                                if st.button("Programı Sil"):
                                    with engine.connect() as conn:
                                        conn.execute(text("DELETE FROM personel_vardiya_programi WHERE id = :id"), {"id": del_id})
                                        conn.commit()
                                    st.success("Silindi!"); time.sleep(0.5); st.rerun()

                        else:
                            st.info("ℹ️ Görüntülenecek program kaydı bulunamadı.")

                    except Exception as e:
                        st.error(f"Liste hatası: {e}")

            # Seçenek listelerini hazırla (Kaldırıldı - yukarı taşındı)
            # (Bu blok daha önce yukarıda tanımlandı)

            # >>> ALT SEKME 1: DÜZENLEME FORMU <<<
            # >>> ALT SEKME 1: DÜZENLEME FORMU <<<
            elif p_selected_tab == p_tabs[1]:
                st.subheader("👤 Personel Bilgilerini Yönet")
                st.caption("Personel eklemek veya mevcut olanı güncellemek için formu doldurun.")

                # Mevcut personel verisini çek (Seçim için)
                pers_df_raw = veri_getir("personel")

                col_sel1, col_sel2 = st.columns([3, 1])
                mod = col_sel1.radio("İşlem Modu", ["➕ Yeni Personel Ekle", "✏️ Mevcut Personeli Düzenle"], horizontal=True)

                selected_pers_id = None
                selected_row = {}

                if mod == "✏️ Mevcut Personeli Düzenle" and not pers_df_raw.empty:
                    # DÜZELTME: İsim yerine ID bazlı seçim (Mükerrer isim sorununu çözer)
                    pers_dict = dict(zip(pers_df_raw['id'], pers_df_raw['ad_soyad']))

                    selected_pers_id = col_sel1.selectbox(
                        "Düzenlenecek Personel",
                        options=pers_dict.keys(),
                        format_func=lambda x: f"{pers_dict[x]} (ID: {x})"
                    )

                    selected_row = pers_df_raw[pers_df_raw['id'] == selected_pers_id].iloc[0]

                with st.form("personel_detay_form"):
                    c1, c2 = st.columns(2)

                    # Form Alanları (DB Standartlarına %100 Uyumlu)
                    p_ad_soyad = c1.text_input("Ad Soyad", value=selected_row.get('ad_soyad', ""))
                    p_gorev = c2.text_input("Görev / Unvan", value=selected_row.get('gorev', ""))
                    p_durum = c2.selectbox("Durum", ["AKTİF", "PASİF"], index=0 if selected_row.get('durum') != "PASİF" else 1)

                    st.divider()

                    c3, c4 = st.columns(2)
                    # Departman ve Yönetici (FK bağlantıları)
                    p_dept_id = c3.selectbox("Departman", options=list(dept_options.keys()),
                                           index=list(dept_options.keys()).index(selected_row.get('departman_id')) if selected_row.get('departman_id') in dept_options else 0,
                                           format_func=lambda x: dept_options[x])
                    p_yonetici_id = c4.selectbox("Bağlı Olduğu Yönetici", options=list(yonetici_options.keys()),
                                               index=list(yonetici_options.keys()).index(selected_row.get('yonetici_id')) if selected_row.get('yonetici_id') in yonetici_options else 0,
                                               format_func=lambda x: yonetici_options[x])

                    # Pozisyon Seviyesi (Organizasyon Şeması Hiyerarşisi için KRİTİK)
                    # DİNAMİK YAPILANDIRMA (constants.py'den gelir)
                    pozisyon_options = {
                        k: f"{k} - {v['name']}" for k,v in POSITION_LEVELS.items()
                    }
                    mevcut_seviye = int(selected_row.get('pozisyon_seviye', 6)) if pd.notna(selected_row.get('pozisyon_seviye')) else 6
                    p_pozisyon = c3.selectbox("📊 Hiyerarşi Seviyesi", options=list(pozisyon_options.keys()),
                                             index=mevcut_seviye,
                                             format_func=lambda x: pozisyon_options[x],
                                             help="Organizasyon şemasındaki konumu belirler")

                    # Ek Sütunlar
                    c5, c6 = st.columns(2)
                    p_kat = c5.text_input("Çalıştığı Kat", value=selected_row.get('kat', ""))
                    p_giris = c6.date_input("İşe Giriş Tarihi", value=pd.to_datetime(selected_row.get('ise_giris_tarihi')).date() if pd.notna(selected_row.get('ise_giris_tarihi')) and selected_row.get('ise_giris_tarihi') != "" else get_istanbul_time().date())

                    c7, c8 = st.columns(2)
                    p_servis = c7.text_input("Servis Durağı", value=selected_row.get('servis_duragi', ""))
                    p_tel = c8.text_input("Telefon No", value=selected_row.get('telefon_no', ""))

                    if st.form_submit_button("💾 Personel Kaydet", use_container_width=True):
                        if p_ad_soyad:
                            try:
                                with engine.connect() as conn:
                                    # DÜZELTME: Daha dayanıklı ID temizleme (0, 0.0, "", "None" vb. durumları NULL yapar)
                                    def robust_id_clean(v):
                                        if pd.isnull(v) or str(v).strip() in ['0', '0.0', 'None', 'nan', '', '0.']: return None
                                        try: return int(float(v))
                                        except: return None

                                    p_yon_val = robust_id_clean(p_yonetici_id)
                                    p_dept_val = robust_id_clean(p_dept_id)

                                    # OTOMATİK ROL ATAMA (Hiyerarşiye Göre)
                                    # Kullanıcı isteği: Hiyerarşik seviyesine göre yetki (rol) otomatik belirlensin.
                                    p_rol = "Personel" # Varsayılan
                                    if p_pozisyon <= 1: p_rol = "Admin" # veya GENEL MÜDÜR
                                    elif p_pozisyon <= 3: p_rol = "ÜRETİM MÜDÜRÜ" # Müdür seviyesi
                                    elif p_pozisyon <= 5: p_rol = "BÖLÜM SORUMLUSU" # Şef/Koordinatör/Sorumlu
                                    else: p_rol = "Personel"

                                    if selected_pers_id:
                                        # GÜNCELLE
                                        # DÜZELTME: Legacy 'bolum' kolonunu da güncelle
                                        p_dept_name = dept_options.get(p_dept_id, "Tanımsız").replace(".. ", "").replace("↳ ", "").strip()

                                        sql = text("""
                                            UPDATE personel
                                            SET ad_soyad=:a, gorev=:g, departman_id=:d, bolum=:bn, yonetici_id=:y,
                                                durum=:st, kat=:k, pozisyon_seviye=:ps, rol=:r,
                                                ise_giris_tarihi=:ig, servis_duragi=:sd, telefon_no=:tn
                                            WHERE id=:id
                                        """)
                                        conn.execute(sql, {
                                            "a":p_ad_soyad, "g":p_gorev, "d":p_dept_val, "bn":p_dept_name, "y":p_yon_val,
                                            "st":p_durum, "k":p_kat, "ps":p_pozisyon, "r":p_rol,
                                            "ig":str(p_giris), "sd":p_servis, "tn":p_tel, "id":selected_pers_id
                                        })
                                    else:
                                        # EKLE
                                        # DÜZELTME: Legacy 'bolum' kolonunu da ekle
                                        p_dept_name = dept_options.get(p_dept_id, "Tanımsız").replace(".. ", "").replace("↳ ", "").strip()

                                        sql = text("""
                                            INSERT INTO personel (ad_soyad, gorev, departman_id, bolum, yonetici_id, durum, kat, pozisyon_seviye, rol, ise_giris_tarihi, servis_duragi, telefon_no)
                                            VALUES (:a, :g, :d, :bn, :y, :st, :k, :ps, :r, :ig, :sd, :tn)
                                        """)
                                        conn.execute(sql, {
                                            "a":p_ad_soyad, "g":p_gorev, "d":p_dept_val, "bn":p_dept_name, "y":p_yon_val,
                                            "st":p_durum, "k":p_kat, "ps":p_pozisyon, "r":p_rol,
                                            "ig":str(p_giris), "sd":p_servis, "tn":p_tel
                                        })
                                    conn.commit()

                                    # Önbellekleri temizle (KRİTİK DÜZELTME)
                                    # Bu işlem yapılmazsa, kullanıcı eski veriyi görmeye devam eder ve
                                    # tekrar kaydettiğinde eski veriyi veritabanına geri yazar!
                                    cached_veri_getir.clear()
                                    get_personnel_hierarchy.clear()
                                    get_user_roles.clear()

                                st.success("✅ İşlem başarıyla tamamlandı!"); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Hata: {e}")
                        else: st.warning("Ad Soyad zorunludur.")


            # >>> ALT SEKME 2: TABLO <<<
            # >>> ALT SEKME 2: TABLO <<<
            elif p_selected_tab == p_tabs[2]:
                st.caption("Tüm personel listesini görüntüleyin ve toplu düzenleme yapın")
                try:
                    # Dinamik bölüm listesini hiyerarşik olarak al (Örn: Üretim > Sos Ekleme)
                    bolum_listesi = get_department_tree()
                    if not bolum_listesi:
                        bolum_listesi = ["Üretim", "Paketleme", "Depo", "Ofis", "Kalite"]

                    # Tüm tabloyu çek
                    pers_df = pd.read_sql("SELECT * FROM personel", engine)

                    # ise_giris_tarihi sütununu string'e çevir (Streamlit'in date olarak algılamasını önle)
                    if 'ise_giris_tarihi' in pers_df.columns:
                        pers_df['ise_giris_tarihi'] = pers_df['ise_giris_tarihi'].astype(str).replace('None', '').replace('nan', '').replace('NaT', '')

                    # Yeni alanlar için dropdown seçeneklerini hazırla
                    # Departman listesi (Foreign Key için ID bazlı)
                    # Yeni alanlar için dropdown seçeneklerini hazırla
                    # Departman listesi (Foreign Key için ID bazlı) - HİYERARŞİK
                    try:
                        dept_id_to_name = get_department_options_hierarchical()
                        # "- Seçiniz -" zaten 0 ID ile geliyor, listede olması yeterli
                        dept_name_list = list(dept_id_to_name.values())
                    except:
                        dept_id_to_name = {}
                        dept_name_list = ["- Seçiniz -"]

                    # Yönetici listesi (Self-referencing FK için ID bazlı)
                    try:
                        yonetici_df = pd.read_sql("SELECT id, ad_soyad FROM personel WHERE ad_soyad IS NOT NULL AND pozisyon_seviye <= 5 ORDER BY ad_soyad", engine)
                        yonetici_id_to_name = {row['id']: row['ad_soyad'] for _, row in yonetici_df.iterrows()}
                        yonetici_name_list = list(yonetici_id_to_name.values())
                        yonetici_name_list.insert(0, "- Yok -")
                    except:
                        yonetici_id_to_name = {}
                        yonetici_name_list = ["- Yok -"]

                    # Pozisyon seviyesi mapping
                    # DİNAMİK LİSTE (constants.py'den gelir)
                    # List formatına çevir (Streamlit selectbox column için)
                    seviye_list = [
                        f"{k} - {v['name']}" for k,v in sorted(POSITION_LEVELS.items())
                    ]

                    # Yardımcı sütunlar ekle (ID -> İsim dönüşümü için)

                    # Yardımcı sütunlar ekle (ID -> İsim dönüşümü için)
                    # DÜZELTME: ID'leri integer'a çevirerek map et (Float/Int uyuşmazlığını önle)
                    # NaNs -> 0 yapıp map edelim
                    pers_df['departman_adi'] = pers_df['departman_id'].fillna(0).astype(int).map(dept_id_to_name)
                    pers_df['departman_adi'] = pers_df['departman_adi'].fillna("- Seçiniz -")

                    # Yönetici ID -> İsim
                    pers_df['yonetici_adi'] = pers_df['yonetici_id'].fillna(0).astype(int).map(yonetici_id_to_name)
                    pers_df['yonetici_adi'] = pers_df['yonetici_adi'].fillna("- Yok -")

                    # Pozisyon Seviye -> Açıklama
                    pers_df['pozisyon_adi'] = pers_df['pozisyon_seviye'].apply(
                        lambda x: seviye_list[int(x)] if pd.notna(x) and 0 <= int(x) <= 7 else "6 - Personel (Varsayılan)"
                    )

                    # KOLON KONUMLANDIRMA (Reorder Columns) - ORİJİNAL SIRALAMA GERİ YÜKLENDİ
                    # Yeni sütunlar (Servis, Telefon) listenin sonuna eklendi, orijinal sıra bozulmadı.
                    desired_order = ['id', 'ad_soyad', 'departman_adi', 'yonetici_adi', 'pozisyon_adi', 'gorev', 'durum', 'ise_giris_tarihi', 'servis_duragi', 'telefon_no']
                    # Geri kalan kolonları da ekle
                    existing_cols = pers_df.columns.tolist()
                    final_cols = desired_order + [c for c in existing_cols if c not in desired_order]
                    # Dataframe'i yeniden sırala
                    pers_df = pers_df[final_cols]

                    # Güvenli MAP İŞLEMİ (Float/Int mismatch önlemi)
                    # Önceden yapılsa da burada garanti altına alıyoruz
                    # Eğer departman_id NaN ise 0 yap, int'e çevir
                    if 'departman_id' in pers_df.columns:
                         pers_df['departman_id_safe'] = pd.to_numeric(pers_df['departman_id'], errors='coerce').fillna(0).astype(int)
                         pers_df['departman_adi'] = pers_df['departman_id_safe'].map(dept_id_to_name).fillna("- Seçiniz -")
                         # (Reassign column in new position is automatic in pandas assignment, no need to reorder again if already ordered,
                         # but assignment might put it at end if not careful. But we already reordered.
                         # Wait, if I assign to a column that exists, order is preserved.)

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
                            "departman_id": None,  # Gizle (Backend ID)
                            "yonetici_id": None,   # Gizle (Backend ID)
                            "departman_adi": st.column_config.SelectboxColumn(
                                "🏭 Departman",
                                options=dept_name_list, # ["Üretim", "  ↳ Fırın"]
                                help="Personelin çalıştığı departman",
                                width="medium",
                                required=True
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
                            "vardiya": None, # Gizle - Artık Vardiya Programı sekmesinden yönetiliyor
                            "durum": st.column_config.SelectboxColumn("Durum", options=["AKTİF", "PASİF"], width="small"),
                            "servis_duragi": st.column_config.TextColumn("Servis Durağı"),
                            "telefon_no": st.column_config.TextColumn("Telefon No"),
                            "ise_giris_tarihi": st.column_config.TextColumn("İşe Giriş", width="small", disabled=False),
                            "sorumlu_bolum": None,  # Gizle - Gereksiz (gorev alanı yeterli)
                            "izin_gunu": None # Gizle - Artık Vardiya Programı sekmesinden yönetiliyor
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
                                    format_func=lambda x: f"{deletable_pers[deletable_pers['id']==x]['ad_soyad'].values[0]} ({deletable_pers[deletable_pers['id']==x][dept_col].values[0]}) [ID:{x}]"
                                    )
                                else:
                                    selected_ids = st.multiselect(
                                        "Silmek istediğiniz personeli seçin:",
                                        options=deletable_pers['id'].tolist(),
                                        format_func=lambda x: f"{deletable_pers[deletable_pers['id']==x]['ad_soyad'].values[0]} [ID:{x}]"
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
                            # İsimden ID'ye geri dönüştürme işlemi ARTIK GEREKSİZ.
                            # Çünkü editör doğrudan ID sütunlarını değiştirdi.

                            # Sadece Pozisyon Seviyesi hala string (Selectbox logic) ise onu çevir
                            # Ama onuda ID'ye çevirebiliriz. Şimdilik eski logic kalsın çünkü pozisyon_options dict değil list olabilir.
                            # Kontrol edelim: pozisyon_options bir dict {0: "...", ...}.
                            # Ama kodda seviye_list kullanılıyor.

                            # Pozisyon Adı -> Seviye (Sayı)
                            # Eğer editörde pozisyon_adi (String) değiştirdiysek:
                            edited_pers['pozisyon_seviye'] = edited_pers['pozisyon_adi'].apply(
                                lambda x: int(x.split(' - ')[0]) if pd.notna(x) and ' - ' in str(x) else 5
                            )

                            # İSİM -> ID DÖNÜŞÜMÜ (Robust Logic)
                            # 1. Departman ID'lerini geri yükle
                            # Sözlükleri tazelemek için (İsim değişiklikleri veya cache sorunlarına karşı)
                            try:
                                current_dept_map = get_department_options_hierarchical()
                            except:
                                current_dept_map = dept_id_to_name

                            # Ters sözlük: "  ↳ Fırın" -> 5
                            # Hem orijinal halini hem de temizlenmiş halini map'e ekle
                            name_to_id_map = {}
                            for d_id, d_name in current_dept_map.items():
                                name_to_id_map[d_name] = d_id
                                name_to_id_map[d_name.strip()] = d_id
                                name_to_id_map[d_name.replace('\u00A0', '').strip()] = d_id

                            def robust_id_clean(v):
                                if pd.isnull(v) or str(v).strip() in ['0', '0.0', 'None', 'nan', '', '0.']: return None
                                try: return int(float(v))
                                except: return None
                            def resolve_dept_id(val):
                                if pd.isna(val) or val == "" or val == "-" or val == "- Seçiniz -": return None
                                # 1. Tam eşleşme
                                if val in name_to_id_map: return name_to_id_map[val]
                                # 2. Temizleyip dene (Unicode NBSP temizliği)
                                clean = str(val).replace('\u00A0', ' ').strip()
                                if clean in name_to_id_map: return name_to_id_map[clean]
                                # 3. Daha agresif temizlik (Tüm boşlukları silip dene)
                                very_clean = clean.replace(' ', '')
                                # Harita anahtarlarını da temizleyip karşılaştır
                                for k, v in name_to_id_map.items():
                                    if str(k).replace('\u00A0', ' ').replace(' ', '').strip() == very_clean:
                                        return v
                                return None

                            edited_pers['departman_id'] = edited_pers['departman_adi'].apply(resolve_dept_id)

                            # 2. Yönetici ID'lerini geri yükle
                            # Ters sözlük oluştur
                            name_to_sup_map = {v: k for k, v in yonetici_id_to_name.items()}
                            edited_pers['yonetici_id'] = edited_pers['yonetici_adi'].map(name_to_sup_map)

                            # DÜZELTME: 0 Değerlerini NULL (None) yap (Postgres FK hatasını önler)
                            edited_pers['yonetici_id'] = edited_pers['yonetici_id'].apply(robust_id_clean)
                            edited_pers['departman_id'] = edited_pers['departman_id'].apply(robust_id_clean)

                            # DÜZELTME: 'bolum' (Text) kolonunu da güncelle (Legacy raporlar için)
                            # departman_adi'ni (ok işaretli olabilir) temizle ve bolum kolonuna kopyala
                            # Regex kullanmadan str.replace yapıyoruz, app.py genelinde standart bu.
                            edited_pers['bolum'] = edited_pers['departman_adi'].astype(str).str.replace(".. ", "", regex=False).str.replace("↳ ", "", regex=False).str.strip()

                            # Yardımcı sütunları kaldır (AMA 'bolum' kalmalı!)
                            # departman_adi, yonetici_adi, pozisyon_adi görsel amaçlıydı, kaldırıyoruz.
                            edited_pers = edited_pers.drop(columns=['departman_adi', 'yonetici_adi', 'pozisyon_adi', 'departman_id_safe'], errors='ignore')

                            # DÜZELTME: to_sql ile 'replace' kullanılamaz çünkü view'lar tabloya bağımlı
                            # Çözüm: TRUNCATE + INSERT kullan (Atomik Transaction ile)

                            # SAFETY CHECK: Departman ID'si kaybolmuş mu?
                            invalid_depts = edited_pers[edited_pers['departman_id'].isna()]
                            if not invalid_depts.empty:
                                st.error("❌ HATA: Bazı personellerin departman bilgisi eşleştirilemedi!")
                                st.dataframe(invalid_depts[['ad_soyad']], hide_index=True)
                                st.warning("Lütfen departman isimlerini kontrol ediniz. Kayıt iptal edildi.")
                            else:
                                try:
                                    # TEK TRANSACTION İÇİNDE SİL VE EKLE
                                    # engine.begin() allows rollback if anything fails
                                    with engine.begin() as conn:
                                        # Departman ID'den temiz isim bulmak için ters harita (Önbellekten veya mevcut map'ten)
                                        clean_dept_names = {d_id: d_name.replace(".. ", "").replace("↳ ", "").strip() for d_id, d_name in current_dept_map.items()}

                                        for idx, row in edited_pers.iterrows():
                                            d_id = row.get('departman_id')
                                            b_name = clean_dept_names.get(d_id, "Tanımsız")

                                            # Eğer ID varsa güncelle, yoksa ekle (Upsert mantığı)
                                            if pd.notna(row.get('id')):
                                                # Mevcut personeli güncelle (Kritik kolonlar -Rol, Şifre- korunur)
                                                update_sql = text("""
                                                    UPDATE personel
                                                    SET ad_soyad=:a, departman_id=:d, bolum=:bn, yonetici_id=:y,
                                                        pozisyon_seviye=:ps, gorev=:g, durum=:st,
                                                        ise_giris_tarihi=:ig, servis_duragi=:sd, telefon_no=:tn
                                                    WHERE id=:id
                                                """)
                                                conn.execute(update_sql, {
                                                    "a": row['ad_soyad'], "d": d_id, "bn": b_name,
                                                    "y": row['yonetici_id'], "ps": row['pozisyon_seviye'], "g": row['gorev'],
                                                    "st": row['durum'], "ig": str(row['ise_giris_tarihi']) if pd.notna(row['ise_giris_tarihi']) else None,
                                                    "sd": row['servis_duragi'], "tn": row['telefon_no'], "id": row['id']
                                                })
                                            else:
                                                # Yeni personeli ekle (Varsayılan Rol atanır)
                                                # OTOMATİK ROL ATAMA (Hiyerarşiye Göre)
                                                p_ps = row['pozisyon_seviye']
                                                if p_ps <= 1: p_rol = "Admin"
                                                elif p_ps <= 3: p_rol = "ÜRETİM MÜDÜRÜ"
                                                elif p_ps <= 5: p_rol = "BÖLÜM SORUMLUSU"
                                                else: p_rol = "Personel"

                                                insert_sql = text("""
                                                    INSERT INTO personel (ad_soyad, departman_id, bolum, yonetici_id, pozisyon_seviye, gorev, durum, ise_giris_tarihi, servis_duragi, telefon_no, rol)
                                                    VALUES (:a, :d, :bn, :y, :ps, :g, :st, :ig, :sd, :tn, :rol)
                                                """)
                                                conn.execute(insert_sql, {
                                                    "a": row['ad_soyad'], "d": d_id, "bn": b_name,
                                                    "y": row['yonetici_id'], "ps": p_ps, "g": row['gorev'],
                                                    "st": row['durum'], "ig": str(row['ise_giris_tarihi']) if pd.notna(row['ise_giris_tarihi']) else None,
                                                    "sd": row['servis_duragi'], "tn": row['telefon_no'], "rol": p_rol
                                                })

                                    # Cache'leri temizle (Sadece başarılıysa buraya gelir)
                                    cached_veri_getir.clear()
                                    get_user_roles.clear()
                                    get_personnel_hierarchy.clear()
                                    st.success("✅ Personel listesi güvenli şekilde güncellendi!")
                                    time.sleep(1); st.rerun()
                                except Exception as save_error:
                                    st.error(f"Kayıt işlemi sırasında kritik hata: {save_error}")
                                    st.info("Veri kaybını önlemek için değişiklikler geri alındı (Rollback).")

                except Exception as e:
                    st.error(f"Personel verisi alınamadı: {e}")

            # ORTAK SYNC BUTONU
            render_sync_button(key_prefix="personel")


        with tab2:
            st.subheader("🔐 Kullanıcı Yetki ve Şifre Yönetimi")

            # Rolleri veritabanından çek (Tüm tab için ortak)
            try:
                roller_df_tab = pd.read_sql("SELECT rol_adi FROM ayarlar_roller WHERE aktif = TRUE ORDER BY id", engine)
                rol_listesi = roller_df_tab['rol_adi'].tolist()
            except:
                rol_listesi = ["PERSONEL", "VARDIYA AMIRI", "BÖLÜM SORUMLUSU", "KALİTE SORUMLUSU", "DEPO SORUMLUSU", "ADMIN", "GENEL KOORDİNATÖR", "Personel", "Vardiya Amiri", "Bölüm Sorumlusu", "Kalite Sorumlusu", "Admin"]

            if not rol_listesi: rol_listesi = ["PERSONEL", "ADMIN"] # Fallback

            # --- YENİ KULLANICI EKLEME BÖLÜMÜ ---
            with st.expander("➕ Sisteme Yeni Kullanıcı Ekle"):
                # Dinamik bölüm listesini hiyerarşik olarak al (Örn: Üretim > Krema)
                bolum_listesi = get_department_tree()
                if not bolum_listesi:
                    bolum_listesi = ["Üretim", "Depo", "Kalite", "Yönetim"]

                # Kullanıcı adı olmayan fabrika personelini çek (potansiyel kullanıcılar)
                parametre_hatasi_yok = True
                try:
                    # TÜM personeli çek (Filtresiz) + Yönetici Adı + Bölüm Adı
                    fabrika_personel_df = pd.read_sql(
                        """
                        SELECT p.*,
                               COALESCE(d.bolum_adi, 'Tanımsız') as bolum_adi_display,
                               y.ad_soyad as yonetici_adi_display
                        FROM personel p
                        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
                        LEFT JOIN personel y ON p.yonetici_id = y.id
                        WHERE p.ad_soyad IS NOT NULL
                        ORDER BY p.ad_soyad
                        """,
                        engine
                    )
                except Exception as sql_error:
                    st.error(f"⚠️ Personel verisi yüklenirken hata: {sql_error}")
                    fabrika_personel_df = pd.DataFrame()
                    parametre_hatasi_yok = False

                # Kaynak: Sadece Mevcut Fabrika Personeli
                st.info("📋 **Personel Yetkilendirme**: Aşağıdaki listeden fabrikadaki bir personeli seçerek şifre ve yetki tanımlayabilirsiniz.")

                # --- FORM YAPISI DEĞİŞTİRİLDİ ---
                if True: # Indentation wrapper

                    # Varsayılan değerler
                    n_departman_id_default = 0
                    n_yonetici_id_default = 0
                    n_pozisyon_seviye_default = 5
                    n_gorev_default = ""

                    if not fabrika_personel_df.empty:
                        # Mevcut personelden seçim (ID BAZLI - EŞSİZLİK İÇİN)
                        # Sözlük oluştur: ID -> İsim (Bölüm)
                        personel_dict = dict(zip(
                            fabrika_personel_df['id'],
                            fabrika_personel_df['ad_soyad'] + " (" + fabrika_personel_df['bolum_adi_display'] + ")"
                        ))

                        # --- ETKİLEŞİM İÇİN FORM DIŞINA ALINDI ---
                        secilen_personel_id = st.selectbox(
                            "👤 Personel Seçin (İsim Yazıp Aratabilirsiniz)",
                            options=fabrika_personel_df['id'].tolist(),
                            format_func=lambda x: personel_dict.get(x, f"ID: {x}"),
                            key="select_personel_id_interactive"
                        )

                        # Seçilen personelin TÜM bilgilerini al (ID ile kesin eşleşme)
                        secilen_row = fabrika_personel_df[fabrika_personel_df['id'] == secilen_personel_id].iloc[0]
                        secilen_personel_adi = secilen_row['ad_soyad']

                        # Bilgileri çıkar (Güvenli .get kullanımı)
                        secilen_bolum = secilen_row.get('bolum_adi_display', 'Tanımsız')
                        secilen_yonetici = secilen_row.get('yonetici_adi_display', 'Yok')
                        mevcut_kullanici = secilen_row.get('kullanici_adi', '')
                        mevcut_rol = secilen_row.get('rol', 'Personel')

                        # Form için varsayılan değerleri ayarla
                        n_departman_id = int(secilen_row.get('departman_id', 0)) if pd.notna(secilen_row.get('departman_id')) else 0
                        n_yonetici_id = int(secilen_row.get('yonetici_id', 0)) if pd.notna(secilen_row.get('yonetici_id')) else 0
                        n_pozisyon_seviye = int(secilen_row.get('pozisyon_seviye', 5)) if pd.notna(secilen_row.get('pozisyon_seviye')) else 5
                        n_gorev = str(secilen_row.get('gorev', '')) if pd.notna(secilen_row.get('gorev')) else ''
                        if secilen_yonetici is None: secilen_yonetici = "Yok" # None check

                        # --- PERSONEL KÜNYESİ (MEVCUT TANIMLAMALAR) ---
                        st.info(f"📋 **SEÇİLEN PERSONEL KARTI**")
                        # 3 Kolonlu Bilgi Kartı
                        k1, k2, k3 = st.columns(3)
                        k1.caption("📍 Departman"); k1.write(f"**{secilen_bolum}**")
                        k2.caption("💼 Görev"); k2.write(f"**{n_gorev if n_gorev else '-'}**")
                        k3.caption("👔 Yönetici"); k3.write(f"**{secilen_yonetici}**")

                        k4, k5, k6 = st.columns(3)
                        k4.caption("📊 Seviye"); k4.write(f"**{n_pozisyon_seviye}**")
                        k5.caption("🆔 Mevcut Kullanıcı"); k5.write(f"`{mevcut_kullanici}`" if mevcut_kullanici else "Yok")
                        k6.caption("🎭 Mevcut Rol"); k6.write(f"**{mevcut_rol}**")

                        if pd.notna(mevcut_kullanici) and mevcut_kullanici != '':
                            st.warning(f"⚠️ Bu personele zaten şifre tanımlanmış. Buradan yapacağınız işlem şifresini ve yetkisini GÜNCELLEYECEKTİR.")

                        n_ad = secilen_personel_adi
                        is_from_personel = True

                        # Kullanıcı Adı Önerisi (logic modülünden)
                        default_user_val = mevcut_kullanici if mevcut_kullanici else suggest_username(secilen_personel_adi)

                        # Dynamic Key Suffix (Kişi değiştikçe inputlar sıfırlansın)
                        key_suffix = f"_{secilen_personel_id}"

                    else:
                        st.warning("⚠️ Fabrika personeli bulunamadı veya veri çekilemedi.")
                        n_ad = ""
                        default_user_val = ""
                        key_suffix = "_none"
                        n_departman_id = 0

                    # --- KULLANICI GİRİŞ BİLGİLERİ (FORM İÇİNDE) ---
                    with st.form("new_user_form"):
                        col1, col2 = st.columns(2)

                        # Kullanıcı Adı ve Şifre
                        n_user = col1.text_input("🔑 Kullanıcı Adı", value=default_user_val, key=f"n_u{key_suffix}")
                        n_pass = col2.text_input("🔒 Şifre", type="password", key=f"n_p{key_suffix}")

                        # Rol seçimi
                        def_rol_index = 0
                        if 'mevcut_rol' in locals() and mevcut_rol in rol_listesi:
                            def_rol_index = rol_listesi.index(mevcut_rol)

                        n_rol = st.selectbox("🎭 Yetki Rolü", rol_listesi, index=def_rol_index, key=f"n_r{key_suffix}")

                        st.caption(f"ℹ️ Not: Kullanıcı yetkisi, personelin mevcut bölümü olan **{secilen_bolum}** için geçerli olacaktır.")

                        if st.form_submit_button("✅ Yetkili Kullanıcıyı Kaydet", type="primary"):
                            if n_user and n_pass:
                                try:
                                    with engine.connect() as conn:
                                        # Sadece UPDATE işlemi (Departman DEĞİŞMEZ)
                                        sql = """UPDATE personel
                                                 SET kullanici_adi = :k, sifre = :s, rol = :r, durum = 'AKTİF'
                                                 WHERE id = :pid"""

                                        # Kullanıcı Adı Eşsizlik Kontrolü (Opsiyonel ama iyi olur)
                                        # Şimdilik basit update yapıyoruz.

                                        conn.execute(text(sql), {
                                            "k": n_user, "s": n_pass, "r": n_rol,
                                            "pid": secilen_personel_id
                                        })
                                        conn.commit()

                                    # Cache'leri temizle
                                    cached_veri_getir.clear()
                                    get_user_roles.clear()
                                    get_personnel_hierarchy.clear()

                                    st.success(f"✅ {n_user} kullanıcısı başarıyla yetkilendirildi!")
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

            if str(current_role).upper() == "ADMIN" or st.session_state.user in ["Emre ÇAVDAR", "EMRE ÇAVDAR", "Admin", "admin"]:
                try:
                    # Dinamik bölüm listesini hiyerarşik olarak al (Örn: Üretim > Krema)
                    bolum_listesi_edit = get_department_tree() # Filtresiz (Tümü)
                    if not bolum_listesi_edit:
                        bolum_listesi_edit = ["Üretim", "Paketleme", "Depo", "Ofis", "Kalite", "Yönetim", "Temizlik"]

                    # Tüm kullanıcıları çek ve sadece Erisim/Yetki alanlarını göster
                    users_df = pd.read_sql(
                        """
                        SELECT p.kullanici_adi, p.sifre, p.rol, p.ad_soyad, p.durum,
                               COALESCE(d.bolum_adi, 'Tanımsız') as bolum
                        FROM personel p
                        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
                        WHERE p.kullanici_adi IS NOT NULL AND p.kullanici_adi != ''
                        ORDER BY bolum, p.ad_soyad
                        """,
                        engine
                    )

                    # Düzenlenecek sütunları seç (Gereksizler atıldı)
                    if not users_df.empty:
                        # Streamlit data_editor için veri tiplerini garantiye alıyoruz
                        # ".0" ile biten float şifreleri temizle (Örn: 9685.0 -> 9685)
                        users_df['sifre'] = users_df['sifre'].astype(str).str.replace(r'\.0$', '', regex=True)

                        # Gösterilecek kolonlar (Geliştirildi: Durum eklendi)
                        edit_df = users_df[['ad_soyad', 'kullanici_adi', 'sifre', 'rol', 'bolum', 'durum']]

                        edited_users = st.data_editor(
                            edit_df,
                            key="user_editor_main",
                            column_config={
                                "ad_soyad": st.column_config.TextColumn("Ad Soyad", disabled=True, width="medium"),
                                "kullanici_adi": st.column_config.TextColumn("Kullanıcı Adı", disabled=True, width="small"),
                                "sifre": st.column_config.TextColumn("Şifre (Düzenlenebilir)", width="small"),
                                "rol": st.column_config.SelectboxColumn("Yetki Rolü", options=rol_listesi, width="medium"),
                                "bolum": st.column_config.TextColumn("Bölüm", disabled=True, width="medium"),
                                "durum": st.column_config.SelectboxColumn("Durum", options=["AKTİF", "PASİF"], width="small")
                            },
                            use_container_width=True,
                            hide_index=True
                        )

                        if st.button("💾 Kullanıcı Ayarlarını Güncelle", use_container_width=True, type="primary"):
                            try:
                                with engine.connect() as conn:
                                    for index, row in edited_users.iterrows():
                                        sql = "UPDATE personel SET sifre = :s, rol = :r, durum = :d WHERE kullanici_adi = :k"
                                        params = {"s": row['sifre'], "r": row['rol'], "d": row['durum'], "k": row['kullanici_adi']}
                                        conn.execute(text(sql), params)
                                    conn.commit()
                                # Cache Temizle
                                cached_veri_getir.clear()
                                get_user_roles.clear()
                                st.success("✅ Kullanıcı bilgileri (Şifre/Rol) güncellendi!")
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
                st.warning("⚠️ Bu alan (Yetki ve Şifre Yönetimi) sadece **Emre ÇAVDAR** tarafından görülebilir.")
                # Salt okunur ama tam tablo
                users_df = pd.read_sql("SELECT kullanici_adi, rol, bolum, servis_duragi, telefon_no FROM personel WHERE kullanici_adi IS NOT NULL", engine)
                st.table(users_df)

            # ORTAK SYNC BUTONU
            render_sync_button(key_prefix="kullanicilar")

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

                # [TEMİZLİK] Kirli verileri (String 'None') temizle
                if 'sorumlu_departman' in u_df.columns:
                    u_df['sorumlu_departman'] = u_df['sorumlu_departman'].replace(['None', 'none', 'nan', ''], None)

                # --- YENİ: DEPARTMAN FİLTRESİ (PERSONEL LİSTESİ GİBİ) ---
                # Kaynak: Tüm Organizasyon Şeması (User Request: "Hepsini seçebilelim")
                # SİSTEMATİK AYRIM: Sadece ÜRETİM tipindekiler gelsin
                dept_list = ["Tümü"] + get_department_tree(filter_tur="ÜRETİM")
                sel_dept = st.selectbox("📌 Bölüm Filtrele (Hızlı Erişim)", dept_list, key="prod_dept_filter")

                # Yedek (Full) Dataframe'i sakla
                full_product_df = u_df.copy()

                # Filtrele
                if sel_dept != "Tümü":
                    u_df = u_df[u_df['sorumlu_departman'] == sel_dept]

                # Column Config
                edited_products = st.data_editor(
                    u_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_products",
                    column_config={
                        "uretim_bolumu": None, # [GİZLE] Mükerrer sütun (Legacy)
                        "urun_adi": st.column_config.TextColumn("Ürün Adı", required=True),
                        "sorumlu_departman": st.column_config.SelectboxColumn(
                            "Sorumlu Departman (Hiyerarşik)",
                            options=dept_list[1:], # [DÜZELTME] "Tümü" seçeneğini çıkar (Assign edilemez)
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
                    # [TEMİZLİK] Kaydetmeden önce String 'None' temizliği (Kritik)
                    if 'sorumlu_departman' in edited_products.columns:
                        edited_products['sorumlu_departman'] = edited_products['sorumlu_departman'].replace(['None', 'none', 'nan', ''], None)

                    final_df = None

                    if sel_dept == "Tümü":
                        # Filtre yoksa direkt kaydet (Ekle/Sil/Güncelle)
                        final_df = edited_products
                    else:
                        # Filtre varsa MERGE işlemi yap (Sadece Güncelleme)
                        # Yeni satır eklemeyi bu modda desteklemek zor, sadece güncelleme alıyoruz
                        try:
                            # Index üzerinden güncelleme
                            full_product_df.set_index("urun_adi", inplace=True)
                            edited_products.set_index("urun_adi", inplace=True)

                            # Update (Varolanları güncelle)
                            full_product_df.update(edited_products)

                            # (Opsiyonel) Yeni eklenenleri de alabiliriz ama ID çakışması riski var
                            # Şimdilik sadece update güvenli
                            final_df = full_product_df.reset_index()
                            st.info("ℹ️ Filtreli modda değişiklikler ana listeye birleştirildi.")
                        except Exception as e:
                            st.error(f"Birleştirme hatası: {e}")
                            final_df = full_product_df # Hata varsa eskisini koru (güvenli)

                    if final_df is not None:
                        final_df.columns = [c.lower().strip() for c in final_df.columns]
                        final_df.to_sql("ayarlar_urunler", engine, if_exists='replace', index=False)
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

            # ORTAK SYNC BUTONU
            render_sync_button(key_prefix="urunler")

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
            render_sync_button(key_prefix="roller")

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
                            "aciklama": st.column_config.TextColumn("Açıklama"),
                            "tur": st.column_config.SelectboxColumn("Kategori (Tür)", options=["ÜRETİM", "İDARİ", "DEPO", "HİZMET"])
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
                                            SET bolum_adi = :b, ana_departman_id = :p, aktif = :act, sira_no = :s, aciklama = :a, tur = :t
                                            WHERE id = :id
                                        """)
                                        conn.execute(sql, {
                                            "b": row['bolum_adi'], "p": pid, "act": row['aktif'],
                                            "b": row['bolum_adi'], "p": pid, "act": row['aktif'],
                                            "s": int(float(row['sira_no'] or 999)) if pd.notna(row['sira_no']) else 999,
                                            "a": row['aciklama'], "t": row['tur'], "id": row['id']
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
            render_sync_button(key_prefix="bolumler")


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
                    moduller = ["Üretim Girişi", "KPI Kontrol", "Personel Hijyen", "Temizlik Kontrol", "Raporlama", "Soğuk Oda", "Ayarlar"]

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

            # ORTAK SYNC BUTONU
            render_sync_button(key_prefix="yetki")

        # 📍 LOKASYON YÖNETİMİ TAB'I (YENİ)
        with tab_lokasyon:
            st.subheader("📍 Lokasyon Yönetimi (Kat > Bölüm > Hat > Ekipman)")
            st.caption("Fabrika lokasyon hiyerarşisini ve sorumlu departmanları buradan yönetebilirsiniz")

            # Departman Listesini Hiyerarşik Çek (Dropdown için)
            lst_bolumler = []
            try:
                b_df = pd.read_sql("SELECT * FROM ayarlar_bolumler WHERE aktif IS TRUE", engine)


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
            render_sync_button(key_prefix="lokasyonlar")

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

            # ORTAK SYNC BUTONU
            render_sync_button(key_prefix="proses")


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
                    # Mevcut Plan Verisini Çek (Mevcut tablo yapısına uygun basit sorgu)
                    plan_query = """
                        SELECT
                            id,
                            COALESCE(kat, kat_bolum) as kat_adi,
                            kat_bolum as bolum_adi,
                            yer_ekipman as temizlenen_alan,
                            siklik,
                            uygulayici,
                            kontrol_eden as kontrolor,
                            kimyasal as kimyasal_adi,
                            uygulama_yontemi as metot_adi,
                            risk as risk_seviyesi
                        FROM ayarlar_temizlik_plani
                        ORDER BY kat, kat_bolum
                    """
                    try:
                        master_df = pd.read_sql(plan_query, engine)
                    except:
                        master_df = pd.DataFrame()

                    # YENİ PLAN EKLEME FORMU
                    with st.expander("➕ Yeni Temizlik Planı Ekle", expanded=True):
                        with st.container(): # Form iptal -> Dinamik seçim için
                            # Veri Hazırlığı

                            # 1. Lokasyonları Çek (BAĞIMSIZ)
                            try:
                                all_locs = pd.read_sql("SELECT id, ad, tip, parent_id FROM lokasyonlar WHERE aktif=1", engine)
                                all_locs['parent_id'] = pd.to_numeric(all_locs['parent_id'], errors='coerce').fillna(0).astype(int)
                                all_locs['id'] = pd.to_numeric(all_locs['id'], errors='coerce').fillna(0).astype(int)
                                if 'tip' not in all_locs.columns: all_locs['tip'] = 'Bölüm'
                            except Exception as e:
                                st.error(f"Lokasyon yüklenemedi: {e}")
                                all_locs = pd.DataFrame(columns=['id', 'ad', 'tip', 'parent_id'])

                            # 2. Kimyasalları Çek (BAĞIMSIZ)
                            try:
                                chems = pd.read_sql("SELECT id, kimyasal_adi FROM kimyasal_envanter", engine)
                            except:
                                try:
                                    chems = pd.read_sql("SELECT id, kimyasal_adi FROM kimyasal_envanter", engine)
                                except:
                                    chems = pd.DataFrame()

                            # 3. Metotları Çek (BAĞIMSIZ - Hata Kaynağı Burasıydı)
                            try:
                                methods = pd.read_sql("SELECT id, metot_adi FROM tanim_metotlar", engine)
                            except:
                                try:
                                    methods = pd.read_sql("SELECT id, metot_adi FROM tanim_metotlar", engine)
                                except Exception as e:
                                    # Hata olsa bile sessiz kal, diğerlerini bozma
                                    methods = pd.DataFrame() # Hata mesajı basmaya gerek yok, boş gelsin yeter

                            # --- KADEMELİ SEÇİM (4 KATMANLI CASCADE) ---
                            # Teknik Dokümana Uygun: Kat > Bölüm > Hat (opsiyonel) > Ekipman/Yapısal Alan

                            st.caption("📍 **Lokasyon Hiyerarşisi** (Kat → Bölüm → Hat → Ekipman)")

                            c_kat, c_bolum, c_hat = st.columns(3)

                            # 1. KAT SEÇİMİ
                            katlar = pd.DataFrame()
                            if not all_locs.empty:
                                katlar = all_locs[all_locs['tip'] == 'Kat']
                                if katlar.empty: # Fallback: Parent'ı 0 olanlar (Hiyerarşinin en tepesi)
                                    katlar = all_locs[all_locs['parent_id'] == 0]

                            if katlar.empty:
                                c_kat.warning("⚠️ Tanımlı KAT bulunamadı.")
                                c_kat.caption("Lütfen 'Ayarlar > Lokasyonlar' menüsünden lokasyon ağacınızı oluşturun.")
                                kat_dict = {}
                            else:
                                kat_dict = {row['id']: row['ad'] for _, row in katlar.iterrows()}

                            sel_kat_id = c_kat.selectbox("🏢 Kat Seçiniz", options=[0] + list(kat_dict.keys()), format_func=lambda x: kat_dict[x] if x!=0 else "Seçiniz...", key="mp_cascade_kat")

                            # 2. BÖLÜM SEÇİMİ (Kat'a bağlı)
                            sel_bolum_id = None
                            bolum_dict = {}

                            if sel_kat_id != 0:
                                # Sadece seçilen kata bağlı BÖLÜM'leri getir
                                bolumler = all_locs[(all_locs['tip'] == 'Bölüm') & (all_locs['parent_id'] == sel_kat_id)]

                                if not bolumler.empty:
                                    bolum_dict = {row['id']: row['ad'] for _, row in bolumler.iterrows()}
                                    sel_bolum_id = c_bolum.selectbox("🏭 Bölüm Seçiniz", options=list(bolum_dict.keys()), format_func=lambda x: bolum_dict[x], key="mp_cascade_bolum")
                                else:
                                    c_bolum.info("Bu katta tanımlı Bölüm yok.")
                                    sel_bolum_id = None
                            else:
                                c_bolum.selectbox("🏭 Bölüm Seçiniz", ["Önce Kat Seçin"], disabled=True, key="mp_cascade_bolum_disabled")

                            # 3. HAT SEÇİMİ (Bölüm'e bağlı - OPSİYONEL)
                            sel_hat_id = None
                            hat_dict = {}

                            if sel_bolum_id:
                                # Seçilen bölüme bağlı HAT'ları getir
                                hatlar = all_locs[(all_locs['tip'] == 'Hat') & (all_locs['parent_id'] == sel_bolum_id)]

                                if not hatlar.empty:
                                    hat_dict = {row['id']: row['ad'] for _, row in hatlar.iterrows()}
                                    # Hat opsiyonel: "Tümü / Hat Yok" seçeneği ekle
                                    sel_hat_id = c_hat.selectbox("🛤️ Hat Seçiniz (Opsiyonel)",
                                                                  options=[0] + list(hat_dict.keys()),
                                                                  format_func=lambda x: hat_dict[x] if x!=0 else "➖ Hat Yok / Tümü",
                                                                  key="mp_cascade_hat")
                                    if sel_hat_id == 0:
                                        sel_hat_id = None  # Hat seçilmedi, bölümden devam
                                else:
                                    c_hat.info("Bu bölümde Hat tanımlı değil.")
                                    sel_hat_id = None
                            else:
                                c_hat.selectbox("🛤️ Hat Seçiniz", ["Önce Bölüm Seçin"], disabled=True, key="mp_cascade_hat_disabled")

                            # 4. ALAN TİPİ ve SEÇİMİ (Hat veya Bölüm'e bağlı)
                            st.divider()
                            c_tip, c_alan = st.columns([1, 2])
                            alan_tipi = c_tip.radio("Temizlenecek Unsur", ["Ekipman / Makine", "Yapısal Alan (Zemin/Duvar)"], horizontal=True, key="mp_alan_tipi")

                            sel_ekipman_id = None
                            sel_yapisal = None

                            # Ekipman parent: Hat varsa Hat'a, yoksa Bölüm'e bağlı
                            ekipman_parent_id = sel_hat_id if sel_hat_id else sel_bolum_id

                            if ekipman_parent_id:
                                if alan_tipi == "Ekipman / Makine":
                                    # Hem Hat'a hem de Bölüm'e bağlı ekipmanları göster (eğer hat seçilmediyse)
                                    if sel_hat_id:
                                        # Sadece seçilen Hat'a bağlı ekipmanlar
                                        ekipmanlar = all_locs[(all_locs['tip'] == 'Ekipman') & (all_locs['parent_id'] == sel_hat_id)]
                                    else:
                                        # Bölüm'e bağlı tüm ekipmanlar + Bölüm'ün hatlarına bağlı ekipmanlar
                                        # 1. Doğrudan bölüme bağlı ekipmanlar
                                        ekip_bolum = all_locs[(all_locs['tip'] == 'Ekipman') & (all_locs['parent_id'] == sel_bolum_id)]
                                        # 2. Bölümün hatlarına bağlı ekipmanlar
                                        hat_ids = all_locs[(all_locs['tip'] == 'Hat') & (all_locs['parent_id'] == sel_bolum_id)]['id'].tolist()
                                        ekip_hat = all_locs[(all_locs['tip'] == 'Ekipman') & (all_locs['parent_id'].isin(hat_ids))] if hat_ids else pd.DataFrame()
                                        # Birleştir
                                        ekipmanlar = pd.concat([ekip_bolum, ekip_hat]).drop_duplicates(subset=['id'])

                                    ekip_dict = {row['id']: row['ad'] for _, row in ekipmanlar.iterrows()}
                                    sel_ekipman_id = c_alan.selectbox("⚙️ Ekipman Seçiniz", options=list(ekip_dict.keys()), format_func=lambda x: ekip_dict[x], key="mp_ekipman") if ekip_dict else None
                                    if not ekip_dict:
                                        parent_info = f"Hat: {hat_dict.get(sel_hat_id, 'Seçili Hat')}" if sel_hat_id else f"Bölüm: {bolum_dict.get(sel_bolum_id, 'Seçili Bölüm')}"
                                        c_alan.warning(f"Bu lokasyonda ({parent_info}) tanımlı ekipman yok.")
                                else:
                                    # Yapısal Alanlar (Statik Liste)
                                    yapisal_list = ["Zemin", "Duvarlar", "Tavan", "Kapılar", "Pencereler", "Aydınlatma Armatürleri", "Havalandırma Izgaraları", "Giderler / Drenaj", "Raflar / Dolaplar", "Elektrik Panoları (Dış)"]
                                    sel_yapisal = c_alan.selectbox("🧱 Yapısal Alan", yapisal_list, key="mp_yapisal")
                            elif sel_bolum_id:
                                c_alan.info("Bölüm seçili, ekipman/alan seçimi yapabilirsiniz.")
                            else:
                                c_alan.selectbox("Detay", ["Önce Bölüm Seçin"], disabled=True, key="mp_alan_disabled")

                            st.divider()
                            st.caption("👥 Sorumluluk ve Onay Matrisi")

                            # 1. PERSONEL LİSTESİ (Temizlik Ekibi - Hiyerarşik Çekim)
                            try:
                                # 1. Tüm Bölümleri Çek (DÜZELTME: ust_bolum_id -> ana_departman_id)
                                depts = pd.read_sql("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler", engine)

                                # 2. Hedef Departmanları Bul (Temizlik, Bulaşık içerenler ve ALT departmanları)
                                target_ids = set()
                                # Temizlik veya Bulaşık kelimesi geçenleri bul (Ana Düğümler)
                                parents = depts[depts['bolum_adi'].str.contains("Temizlik|Bulaşık", case=False, na=False)]
                                target_ids.update(parents['id'].tolist())

                                # Alt Departmanları Bul (Recursive Loop)
                                # Basit bir döngü ile 3 seviye alta kadar inelim
                                current_parents = list(target_ids)
                                for _ in range(3):
                                    children = depts[depts['ana_departman_id'].isin(current_parents)]
                                    if children.empty: break
                                    new_ids = children['id'].tolist()
                                    target_ids.update(new_ids)
                                    current_parents = new_ids

                                # 3. Personeli Sorgula
                                if target_ids:
                                    ids_tuple = tuple(target_ids)
                                    if len(ids_tuple) == 1: ids_tuple = f"({ids_tuple[0]})"

                                    clean_staff_df = pd.read_sql(f"""
                                        SELECT ad_soyad FROM personel
                                        WHERE durum='AKTİF' AND (
                                            departman_id IN {ids_tuple} OR
                                            bolum LIKE '%Temizlik%' OR
                                            bolum LIKE '%Bulaşık%' OR
                                            gorev LIKE '%Temizlik%' OR
                                            gorev LIKE '%Meydancı%'
                                        ) ORDER BY ad_soyad
                                    """, engine)
                                else:
                                    # Departman bulunamadı, text aramaya devam
                                    clean_staff_df = pd.read_sql("""
                                        SELECT ad_soyad FROM personel
                                        WHERE durum='AKTİF' AND (
                                            bolum LIKE '%Temizlik%' OR
                                            bolum LIKE '%Bulaşık%' OR
                                            gorev LIKE '%Temizlik%' OR
                                            gorev LIKE '%Meydancı%'
                                        ) ORDER BY ad_soyad
                                    """, engine)

                                clean_staff = clean_staff_df['ad_soyad'].tolist()
                            except Exception as e:
                                # Hata durumunda boş değil, hatayı görelim (Lokal debug için faydalı olabilir)
                                st.warning(f"Personel listesi yüklenirken hata: {e}")
                                clean_staff = []

                            if not clean_staff: clean_staff = ["Tanımsız (Lütfen Personel Modülünden Ekleyin)"]

                            # 2. ROLLER (Kontrolörler için)
                            try:
                                roles_df = pd.read_sql("SELECT DISTINCT rol_adi FROM ayarlar_yetkiler ORDER BY rol_adi", engine)
                                roles = roles_df['rol_adi'].tolist()
                            except: roles = []
                            if not roles: roles = ["BÖLÜM SORUMLUSU", "VARDIYA AMIRI", "KALİTE GÜVENCE", "ÜRETİM MÜDÜRÜ", "Bölüm Sorumlusu", "Vardiya Amiri"]

                            c_s1, c_s2, c_s3 = st.columns(3)

                            # A. UYGULAYICI (Kişi Bazlı)
                            sel_uygulayici = c_s1.selectbox("🧹 Uygulayıcı Personel", clean_staff, key="mp_staff")

                            # B. 1. KONTROL (Saha Onayı)
                            # Default: Vardiya Amiri veya Bölüm Sorumlusu
                            def_idx_1 = 0
                            # Case-insensitive ve İ/I duyarlı index bulma
                            roles_upper = [str(r).upper().replace('İ','I') for r in roles]
                            if "VARDIYA AMIRI" in roles_upper:
                                def_idx_1 = roles_upper.index("VARDIYA AMIRI")
                            elif "BOLUM SORUMLUSU" in roles_upper:
                                def_idx_1 = roles_upper.index("BOLUM SORUMLUSU")
                            elif "VARDIYA AMİRİ" in roles_upper:
                                def_idx_1 = roles_upper.index("VARDIYA AMİRİ")
                            elif "BÖLÜM SORUMLUSU" in roles_upper:
                                def_idx_1 = roles_upper.index("BÖLÜM SORUMLUSU")
                            sel_ctrl1 = c_s2.selectbox("👷 1. Kontrol (Saha Sorumlusu)", roles, index=def_idx_1, key="mp_ctrl1")

                            # C. 2. KONTROL (Verifikasyon)
                            # Default: Kalite Güvence
                            def_idx_2 = roles.index("Kalite Güvence") if "Kalite Güvence" in roles else (len(roles)-1 if len(roles)>0 else 0)
                            sel_ctrl2 = c_s3.selectbox("🧪 2. Kontrol (Kalite & Verifikasyon)", roles, index=def_idx_2, key="mp_ctrl2")

                            col4, col5, col6 = st.columns(3)
                            sel_risk = col4.selectbox("Risk Seviyesi", ["Düşük", "Orta", "Yüksek"], key="mp_risk")
                            sel_freq = col5.selectbox("Sıklık", ["Her Vardiya", "Günlük", "Haftalık", "Aylık", "3 Aylık", "Yıllık", "Üretim Sonrası", "İhtiyaç Halinde"], key="mp_freq")

                            chem_dict = {row['id']: row['kimyasal_adi'] for _, row in chems.iterrows()}
                            sel_chem = col6.selectbox("Kimyasal", options=[0] + list(chem_dict.keys()), format_func=lambda x: chem_dict[x] if x!=0 else "Yok", key="mp_chem")

                            meth_dict = {row['id']: row['metot_adi'] for _, row in methods.iterrows()}
                            sel_meth = st.selectbox("Yöntem", options=[0] + list(meth_dict.keys()), format_func=lambda x: meth_dict[x] if x!=0 else "Standart", key="mp_meth")

                            col7, col8 = st.columns(2)
                            sel_valid = col7.selectbox("Validasyon Sıklığı", ["-", "Her Yıkama", "Günlük", "Haftalık", "Aylık"], key="mp_valid")
                            sel_verif = col8.selectbox("Verifikasyon (Doğrulama)", ["Görsel Kontrol", "ATP", "Swap", "Allerjen Kit", "Mikrobiyolojik Analiz"], key="mp_verif")

                            if st.button("💾 Planı Kaydet", type="primary", use_container_width=True, key="btn_save_master_plan_v2"):
                                # Lokasyon belirleme: Hat varsa Hat, yoksa Bölüm
                                lokasyon_kayit_id = sel_hat_id if sel_hat_id else sel_bolum_id

                                if lokasyon_kayit_id and (sel_ekipman_id or sel_yapisal):
                                    try:
                                        with engine.connect() as conn:
                                            # Kat ve Bölüm adlarını al (eski yapı için)
                                            kat_adi = kat_dict.get(sel_kat_id, "") if sel_kat_id else ""
                                            bolum_adi = bolum_dict.get(sel_bolum_id, "") if sel_bolum_id else ""
                                            hat_adi = hat_dict.get(sel_hat_id, "") if sel_hat_id else ""

                                            # Ekipman veya Yapısal Alan adını al
                                            if sel_ekipman_id:
                                                ekip_row = all_locs[all_locs['id'] == sel_ekipman_id]
                                                yer_ekipman_adi = ekip_row.iloc[0]['ad'] if not ekip_row.empty else ""
                                            else:
                                                yer_ekipman_adi = sel_yapisal or ""

                                            # Kat-Bölüm-Hat birleşik ismi (kat_bolum sütunu için)
                                            if hat_adi:
                                                kat_bolum_str = f"{kat_adi} > {bolum_adi} > {hat_adi}"
                                            else:
                                                kat_bolum_str = f"{kat_adi} > {bolum_adi}"

                                            # Kimyasal adını al
                                            kimyasal_adi = chem_dict.get(sel_chem, "") if sel_chem and sel_chem != 0 else ""

                                            # Yöntem adını al
                                            yontem_adi = meth_dict.get(sel_meth, "") if sel_meth and sel_meth != 0 else ""

                                            # ESKİ YAPI İÇİN KAYIT (Mevcut veritabanıyla uyumlu)
                                            # Mevcut sütunlar: kat_bolum, yer_ekipman, risk, siklik, kimyasal,
                                            #                  uygulama_yontemi, validasyon, uygulayici, kontrol_eden,
                                            #                  kayit_no, validasyon_siklik, verifikasyon, verifikasyon_siklik, kat
                                            ins_sql = """
                                                INSERT INTO ayarlar_temizlik_plani
                                                (kat_bolum, yer_ekipman, risk, siklik, kimyasal,
                                                 uygulama_yontemi, validasyon, uygulayici, kontrol_eden,
                                                 validasyon_siklik, verifikasyon, verifikasyon_siklik, kat)
                                                VALUES (:kb, :ye, :r, :s, :k, :uy, :val, :uygulayici, :kontrol,
                                                        :val_s, :verif, :verif_s, :kat)
                                            """

                                            conn.execute(text(ins_sql), {
                                                "kb": kat_bolum_str,
                                                "ye": yer_ekipman_adi,
                                                "r": sel_risk,
                                                "s": sel_freq,
                                                "k": kimyasal_adi,
                                                "uy": yontem_adi,
                                                "val": sel_valid,
                                                "uygulayici": sel_uygulayici,
                                                "kontrol": f"{sel_ctrl1} / {sel_ctrl2}",
                                                "val_s": sel_valid,
                                                "verif": sel_verif,
                                                "verif_s": sel_freq,  # Verifikasyon sıklığı = temizlik sıklığı
                                                "kat": kat_adi
                                            })
                                            conn.commit()
                                        st.success("✅ Temizlik planı kaydedildi!")
                                        time.sleep(1); st.rerun()
                                    except Exception as e:
                                        st.error(f"Kayıt Hatası: {e}")
                                else:
                                    st.warning("Lütfen seçimleri tamamlayın (Kat/Bölüm ve Ekipman/Yapısal Alan).")

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
            render_sync_button(key_prefix="kimyasal")

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
                            # Sütunları modül fonksiyonu ile eşleştir
                            col_map = {
                                "kategori": find_excel_column(df_imp, ['KATEGORİ', 'KATEGORI', 'CATEGORY', 'GRUP']),
                                "soru": find_excel_column(df_imp, ['SORU', 'METNİ', 'METNI', 'TEXT', 'QUESTION']),
                                "risk": find_excel_column(df_imp, ['RİSK', 'RISK', 'PUAN']),
                                "brc": find_excel_column(df_imp, ['BRC', 'REF']),
                                "frekans": find_excel_column(df_imp, ['FREKANS', 'FREQUENCY', 'SIKLIK'])
                            }


                            if not col_map["soru"]:
                                st.error(f"❌ Hata: Excel dosyasında 'SORU' sütunu bulunamadı. Mevcut başlıklar: {list(df_imp.columns)}")
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
            render_sync_button(key_prefix="gmp_soru")





# --- UYGULAMAYI BAŞLAT ---
if __name__ == "__main__":
    if st.session_state.logged_in:
        main_app()
    else:
        login_screen()
