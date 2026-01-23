# 🔧 EKLERİSTAN QMS - Teknik Dokümantasyon

## İçindekiler

1. [Sistem Mimarisi](#1-sistem-mimarisi)
2. [Veritabanı Şeması](#2-veritabanı-şeması)
3. [RBAC Yetkilendirme Sistemi](#3-rbac-yetkilendirme-sistemi)
4. [Cache Sistemi](#4-cache-sistemi)
5. [Fonksiyon Referansı](#5-fonksiyon-referansı)
6. [Deployment](#6-deployment)
7. [Performans Optimizasyonu](#7-performans-optimizasyonu)
8. [Güvenlik](#8-güvenlik)

---

## 1. Sistem Mimarisi

### 1.1 Genel Mimari

```mermaid
graph TB
    A[Streamlit Frontend] --> B[SQLAlchemy ORM]
    B --> C{Veritabanı}
    C -->|Yerel| D[SQLite]
    C -->|Cloud| E[Supabase PostgreSQL]
    A --> F[Graphviz]
    A --> G[Pandas]
    F --> H[PDF Export]
    G --> I[Excel Export]
```

### 1.2 Teknoloji Stack

| Katman | Teknoloji | Versiyon | Amaç |
|--------|-----------|----------|------|
| **Frontend** | Streamlit | 1.x | Web UI framework |
| **Backend** | Python | 3.8+ | Ana uygulama dili |
| **ORM** | SQLAlchemy | 2.x | Veritabanı soyutlama |
| **Veritabanı** | PostgreSQL | 14+ | Cloud production DB |
| **Veritabanı** | SQLite | 3.x | Yerel development DB |
| **Görselleştirme** | Graphviz | 0.20+ | Organizasyon şeması |
| **Data Processing** | Pandas | 2.x | Veri manipülasyonu |
| **PDF** | FPDF | 1.7+ | PDF oluşturma |
| **Excel** | openpyxl | 3.x | Excel export |
| **Timezone** | pytz | 2023+ | İstanbul saat dilimi |

### 1.3 Proje Yapısı

```
EKLERİSTAN_QMS/
├── app.py                      # Ana uygulama dosyası (3713 satır)
├── constants.py                # Pozisyon seviyeleri ve sabitler
├── requirements.txt            # Python bağımlılıkları
├── packages.txt                # Sistem bağımlılıkları (Graphviz)
├── ekleristan_local.db         # SQLite veritabanı (yerel)
├── .streamlit/
│   └── config.toml             # Streamlit konfigürasyonu
├── sql/
│   ├── supabase_personel_org_restructure.sql
│   ├── rbac_database_setup.sql
│   └── ... (25 migration dosyası)
├── docs/
│   ├── KULLANICI_KILAVUZU.md
│   ├── TEKNIK_DOKUMANTASYON.md
│   └── TEST_SENARYOLARI.md
└── README.md
```

---

## 2. Veritabanı Şeması

### 2.1 Ana Tablolar

#### `personel` - Kullanıcı ve Personel Bilgileri

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | INTEGER | Primary Key |
| `ad_soyad` | TEXT | Personel adı |
| `kullanici_adi` | TEXT | Sistem giriş adı (UNIQUE) |
| `sifre` | TEXT | Şifre (plain text) |
| `rol` | TEXT | Kullanıcı rolü |
| `gorev` | TEXT | İş tanımı |
| `bolum` | TEXT | Bölüm adı (legacy) |
| `departman_id` | INTEGER | FK → ayarlar_bolumler |
| `yonetici_id` | INTEGER | FK → personel (self-reference) |
| `pozisyon_seviye` | INTEGER | 0-6 arası seviye |
| `vardiya` | TEXT | Vardiya bilgisi |
| `durum` | TEXT | AKTİF / PASİF |

**İndeksler:**
- `idx_personel_departman` on `departman_id`
- `idx_personel_yonetici` on `yonetici_id`
- `idx_personel_seviye` on `pozisyon_seviye`

#### `ayarlar_bolumler` - Departman Hiyerarşisi

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | INTEGER | Primary Key |
| `bolum_adi` | TEXT | Departman adı |
| `ana_departman_id` | INTEGER | FK → ayarlar_bolumler (recursive) |
| `aktif` | BOOLEAN | Aktif/Pasif |
| `sira_no` | INTEGER | Sıralama |
| `aciklama` | TEXT | Açıklama |

**Özellik:** Sınırsız derinlikte hiyerarşi desteği (recursive foreign key)

#### `ayarlar_roller` - Rol Tanımları

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | INTEGER | Primary Key |
| `rol_adi` | TEXT | Rol adı (UNIQUE) |
| `aciklama` | TEXT | Rol açıklaması |
| `aktif` | BOOLEAN | Aktif/Pasif |
| `olusturma_tarihi` | TIMESTAMP | Oluşturulma zamanı |

#### `ayarlar_yetkiler` - Yetki Matrisi

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | INTEGER | Primary Key |
| `rol_adi` | TEXT | FK → ayarlar_roller |
| `modul_adi` | TEXT | Modül adı |
| `erisim_turu` | TEXT | Yok / Görüntüle / Düzenle |

**Composite Key:** `(rol_adi, modul_adi)`

#### `depo_giris_kayitlari` - Üretim Kayıtları

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | INTEGER | Primary Key |
| `tarih` | DATE | Üretim tarihi |
| `vardiya` | TEXT | Vardiya |
| `kullanici` | TEXT | Kayıt eden |
| `islem_tipi` | TEXT | URETIM / DEPO |
| `urun` | TEXT | Ürün adı |
| `lot_no` | TEXT | Lot numarası |
| `miktar` | REAL | Üretim miktarı |
| `fire` | REAL | Fire miktarı |
| `notlar` | TEXT | Açıklama |
| `zaman_damgasi` | TIMESTAMP | Kayıt zamanı |

#### `urun_kpi_kontrol` - Kalite Kontrol Kayıtları

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | INTEGER | Primary Key |
| `tarih` | DATE | Analiz tarihi |
| `saat` | TIME | Analiz saati |
| `vardiya` | TEXT | Vardiya |
| `urun` | TEXT | Ürün adı |
| `lot_no` | TEXT | Lot numarası |
| `stt` | DATE | Son Tüketim Tarihi |
| `numune_no` | TEXT | Numune sayısı |
| `olcum1` | REAL | Parametre 1 ortalama |
| `olcum2` | REAL | Parametre 2 ortalama |
| `olcum3` | REAL | Parametre 3 ortalama |
| `karar` | TEXT | ONAY / RED |
| `kullanici` | TEXT | Analist |
| `tat` | TEXT | Uygun / Uygun Değil |
| `goruntu` | TEXT | Uygun / Uygun Değil |
| `notlar` | TEXT | Detaylı veri (JSON) |

#### `gmp_soru_havuzu` - GMP Soru Bankası

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | INTEGER | Primary Key |
| `soru_metni` | TEXT | Soru içeriği |
| `kategori` | TEXT | Hijyen / Altyapı / Personel |
| `brc_ref` | TEXT | BRC referans kodu |
| `frekans` | TEXT | GÜNLÜK / HAFTALIK / AYLIK |
| `risk_puani` | INTEGER | 1-3 arası |
| `lokasyon_ids` | TEXT | Virgülle ayrılmış ID'ler |
| `aktif` | BOOLEAN | Aktif/Pasif |

#### `gmp_denetim_kayitlari` - GMP Denetim Sonuçları

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | INTEGER | Primary Key |
| `tarih` | DATE | Denetim tarihi |
| `saat` | TIME | Denetim saati |
| `kullanici` | TEXT | Denetçi |
| `lokasyon_id` | INTEGER | FK → tanim_bolumler |
| `soru_id` | INTEGER | FK → gmp_soru_havuzu |
| `durum` | TEXT | UYGUN / UYGUN DEĞİL |
| `fotograf_yolu` | TEXT | Fotoğraf dosya adı |
| `notlar` | TEXT | Açıklama |
| `brc_ref` | TEXT | BRC referans |
| `risk_puani` | INTEGER | Risk seviyesi |

### 2.2 View'lar

#### `v_organizasyon_semasi` - Organizasyon Şeması View

```sql
CREATE OR REPLACE VIEW v_organizasyon_semasi AS
SELECT 
    p.id,
    p.ad_soyad,
    p.gorev,
    p.rol,
    p.pozisyon_seviye,
    p.yonetici_id,
    y.ad_soyad as yonetici_adi,
    COALESCE(d.bolum_adi, p.bolum, 'Tanımsız') as departman,
    d.id as departman_id,
    p.kullanici_adi,
    p.durum,
    p.vardiya
FROM personel p
LEFT JOIN personel y ON p.yonetici_id = y.id
LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
WHERE p.ad_soyad IS NOT NULL
ORDER BY p.pozisyon_seviye, p.ad_soyad;
```

**Amaç:** Organizasyon şeması için optimize edilmiş veri çekme

---

## 3. RBAC Yetkilendirme Sistemi

### 3.1 Rol Hiyerarşisi

```mermaid
graph TD
    A[Admin] --> B[Yönetim]
    B --> C[Kalite Sorumlusu]
    C --> D[Vardiya Amiri]
    D --> E[Bölüm Sorumlusu]
    E --> F[Personel]
```

### 3.2 Modül Eşlemesi

**`constants.py` içinde tanımlı:**

```python
MODUL_ESLEME = {
    "🏭 Üretim Girişi": "Üretim Girişi",
    "🍩 KPI & Kalite Kontrol": "KPI Kontrol",
    "🛡️ GMP Denetimi": "GMP Denetimi",
    "🧼 Personel Hijyen": "Personel Hijyen",
    "🧹 Temizlik Kontrol": "Temizlik Kontrol",
    "📊 Kurumsal Raporlama": "Raporlama",
    "⚙️ Ayarlar": "Ayarlar"
}
```

### 3.3 Yetki Kontrol Fonksiyonları

#### `kullanici_yetkisi_getir(rol_adi, modul_adi)`

**Amaç:** Veritabanından rol-modül yetki ilişkisini çeker

**Parametreler:**
- `rol_adi` (str): Rol adı
- `modul_adi` (str): Modül adı

**Dönüş:** `"Yok"` | `"Görüntüle"` | `"Düzenle"`

**Cache:** TTL = 300 saniye (5 dakika)

```python
@st.cache_data(ttl=300)
def kullanici_yetkisi_getir(rol_adi, modul_adi):
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
```

#### `kullanici_yetkisi_var_mi(menu_adi, gereken_yetki)`

**Amaç:** Kullanıcının modüle erişim yetkisini kontrol eder

**Parametreler:**
- `menu_adi` (str): Menü adı (emoji ile)
- `gereken_yetki` (str): `"Görüntüle"` veya `"Düzenle"`

**Dönüş:** `bool`

**Özel Durum:** Admin her zaman `True` döner

```python
def kullanici_yetkisi_var_mi(menu_adi, gereken_yetki="Görüntüle"):
    user_rol = st.session_state.get('user_rol', 'Personel')
    
    # Admin bypass
    if user_rol == 'Admin':
        return True
    
    modul_adi = MODUL_ESLEME.get(menu_adi, menu_adi)
    erisim = kullanici_yetkisi_getir(user_rol, modul_adi)
    
    if gereken_yetki == "Görüntüle":
        return erisim in ["Görüntüle", "Düzenle"]
    elif gereken_yetki == "Düzenle":
        return erisim == "Düzenle"
    return False
```

### 3.4 Bölüm Bazlı Filtreleme

#### `bolum_bazli_urun_filtrele(urun_df)`

**Amaç:** Bölüm Sorumlusu rolündeki kullanıcılar için ürün listesini filtreler

**Mantık:**
1. Admin/Yönetim/Kalite → Tüm ürünler
2. Bölüm Sorumlusu → Sadece kendi bölümünün ürünleri
3. Hiyerarşik eşleşme: `"Üretim > Pataşu"` içinde `"Pataşu"` geçiyorsa göster

```python
def bolum_bazli_urun_filtrele(urun_df):
    user_rol = st.session_state.get('user_rol', 'Personel')
    user_bolum = st.session_state.get('user_bolum', '')
    
    if user_rol in ['Admin', 'Yönetim', 'Kalite Sorumlusu', 'Vardiya Amiri']:
        return urun_df
    
    if 'sorumlu_departman' in urun_df.columns and user_bolum:
        mask_bos = urun_df['sorumlu_departman'].isna() | (urun_df['sorumlu_departman'] == '')
        mask_eslesme = urun_df['sorumlu_departman'].astype(str).str.contains(str(user_bolum), case=False, na=False)
        return urun_df[mask_bos | mask_eslesme]
    
    return urun_df
```

---

## 4. Cache Sistemi

### 4.1 Cache Stratejisi

EKLERİSTAN QMS, performans optimizasyonu için Streamlit'in `@st.cache_data` ve `@st.cache_resource` dekoratörlerini kullanır.

### 4.2 Cache Türleri

#### Resource Cache - Veritabanı Bağlantısı

```python
@st.cache_resource
def init_connection():
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
        return create_engine(
            db_url, 
            pool_size=10, 
            max_overflow=20, 
            pool_pre_ping=True,
            pool_recycle=300
        )
    else:
        db_url = 'sqlite:///ekleristan_local.db'
        return create_engine(db_url, connect_args={'check_same_thread': False})
```

**Özellikler:**
- Connection pooling (10 + 20 overflow)
- Pre-ping: Bağlantı kopmalarını otomatik algıla
- Recycle: 5 dakikada bir bağlantıları yenile

#### Data Cache - Sorgu Sonuçları

| Fonksiyon | TTL | Amaç |
|-----------|-----|------|
| `run_query()` | 600s | Genel SQL sorguları |
| `get_user_roles()` | 3600s | Rol listeleri |
| `get_department_hierarchy()` | 600s | Departman hiyerarşisi |
| `get_personnel_hierarchy()` | 5s | Organizasyon şeması (sık değişir) |
| `cached_veri_getir()` | 60s | Tablo verileri |
| `kullanici_yetkisi_getir()` | 300s | Yetki sorguları |

### 4.3 Cache Invalidation

**Manuel Temizleme:**

```python
# Tüm cache'i temizle
st.cache_data.clear()

# Belirli fonksiyonu temizle
cached_veri_getir.clear()
```

**Otomatik Temizleme:**

Veri değişikliği sonrası:

```python
if guvenli_kayit_ekle("Depo_Giris_Kayitlari", yeni_kayit):
    cached_veri_getir.clear()  # Cache'i temizle
    st.success("Kaydedildi!")
    st.rerun()  # Sayfayı yenile
```

---

## 5. Fonksiyon Referansı

### 5.1 Veritabanı Fonksiyonları

#### `veri_getir(tablo_adi)`

**Amaç:** Belirli tablodan veri çeker (cached)

**Parametreler:**
- `tablo_adi` (str): Tablo adı (örn: `"Ayarlar_Personel"`)

**Dönüş:** `pd.DataFrame`

**Desteklenen Tablolar:**
- `Ayarlar_Personel`
- `Ayarlar_Urunler`
- `Depo_Giris_Kayitlari`
- `Ayarlar_Fabrika_Personel`
- `Ayarlar_Temizlik_Plani`
- `Tanim_Bolumler`
- `Kimyasal_Envanter`
- `GMP_Soru_Havuzu`
- `Ayarlar_Bolumler`

#### `guvenli_kayit_ekle(tablo_adi, veri)`

**Amaç:** Veritabanına güvenli kayıt ekleme

**Parametreler:**
- `tablo_adi` (str): Hedef tablo
- `veri` (list): Sıralı veri listesi

**Dönüş:** `bool` (Başarı/Hata)

**Desteklenen Tablolar:**
- `Depo_Giris_Kayitlari`
- `Urun_KPI_Kontrol`

### 5.2 Yardımcı Fonksiyonlar

#### `get_istanbul_time()`

**Amaç:** İstanbul saat diliminde şu anki zamanı döndürür

**Dönüş:** `datetime` object

```python
def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
```

#### `get_position_name(level)` - constants.py

**Amaç:** Pozisyon seviyesinden isim döndürür

**Parametreler:**
- `level` (int): 0-6 arası seviye

**Dönüş:** `str`

**Eşleme:**
- 0 → "Yönetim Kurulu"
- 1 → "Genel Müdür"
- 2 → "Direktörler"
- 3 → "Müdürler"
- 4 → "Şef/Koordinatör"
- 5 → "Personel"
- 6 → "Stajyer/Geçici"

---

## 6. Deployment

### 6.1 Yerel Deployment

**Gereksinimler:**
- Python 3.8+
- pip

**Adımlar:**

```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. Graphviz yükle (Windows)
choco install graphviz

# 3. Uygulamayı başlat
streamlit run app.py
```

### 6.2 Streamlit Cloud Deployment

**Adım 1: GitHub'a Push**

```bash
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main
```

**Adım 2: Streamlit Cloud Konfigürasyonu**

1. [share.streamlit.io](https://share.streamlit.io) → New App
2. Repository seç: `emrecavdar83/EKLER-STAN_QMS`
3. Branch: `main`
4. Main file: `app.py`

**Adım 3: Secrets Ekle**

```toml
# .streamlit/secrets.toml
DB_URL = "postgresql://user:password@host:5432/database"
```

**Adım 4: Advanced Settings**

```toml
# .streamlit/config.toml
[server]
maxUploadSize = 200
enableCORS = false

[theme]
primaryColor = "#8B0000"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
```

### 6.3 Supabase Kurulumu

**Adım 1: Proje Oluştur**

1. [supabase.com](https://supabase.com) → New Project
2. Proje adı: `ekleristan-qms`
3. Database password belirle
4. Region: `Europe (Frankfurt)`

**Adım 2: Connection String Al**

Settings → Database → Connection String → URI

```
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Adım 3: SQL Migration Çalıştır**

SQL Editor'de sırayla çalıştır:

1. `sql/supabase_personel_org_restructure.sql`
2. `sql/rbac_database_setup.sql`
3. `sql/database_indexes.sql`
4. Diğer migration dosyaları

**Adım 4: RLS (Row Level Security) Devre Dışı Bırak**

> ⚠️ Production'da RLS kullanılması önerilir

```sql
ALTER TABLE personel DISABLE ROW LEVEL SECURITY;
ALTER TABLE ayarlar_bolumler DISABLE ROW LEVEL SECURITY;
-- Diğer tablolar için tekrarla
```

---

## 7. Performans Optimizasyonu

### 7.1 Veritabanı İndeksleri

```sql
-- Personel tablosu
CREATE INDEX IF NOT EXISTS idx_personel_departman ON personel(departman_id);
CREATE INDEX IF NOT EXISTS idx_personel_yonetici ON personel(yonetici_id);
CREATE INDEX IF NOT EXISTS idx_personel_seviye ON personel(pozisyon_seviye);

-- Üretim kayıtları
CREATE INDEX IF NOT EXISTS idx_depo_tarih ON depo_giris_kayitlari(tarih);
CREATE INDEX IF NOT EXISTS idx_depo_urun ON depo_giris_kayitlari(urun);

-- GMP kayıtları
CREATE INDEX IF NOT EXISTS idx_gmp_tarih ON gmp_denetim_kayitlari(tarih);
CREATE INDEX IF NOT EXISTS idx_gmp_lokasyon ON gmp_denetim_kayitlari(lokasyon_id);
```

### 7.2 Query Optimizasyonu

**Kötü:**
```python
# Her seferinde tüm tabloyu çek
df = pd.read_sql("SELECT * FROM depo_giris_kayitlari", engine)
df_filtered = df[df['tarih'] == today]
```

**İyi:**
```python
# Filtreyi SQL seviyesinde uygula
sql = "SELECT * FROM depo_giris_kayitlari WHERE tarih = :t"
df = pd.read_sql(text(sql), engine, params={"t": today})
```

### 7.3 Streamlit Optimizasyonu

**Fragment Kullanımı:**

```python
@st.fragment
def expensive_component():
    # Sadece bu bölüm yeniden render edilir
    data = fetch_data()
    st.dataframe(data)
```

**Session State:**

```python
# Veriyi session state'de sakla
if 'data' not in st.session_state:
    st.session_state.data = fetch_expensive_data()

# Tekrar kullan
df = st.session_state.data
```

---

## 8. Güvenlik

### 8.1 Şifre Yönetimi

> ⚠️ **Kritik Güvenlik Açığı:** Şifreler plain text olarak saklanıyor!

**Mevcut Durum:**
```python
# Güvensiz!
db_pass = str(u_data.iloc[0]['sifre']).strip()
if input_pass == db_pass:
    # Giriş başarılı
```

**Önerilen Çözüm:**

```python
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Kayıt
hashed = hash_password("12345")
# DB'ye hashed değeri kaydet

# Giriş
if hash_password(input_pass) == db_hashed:
    # Giriş başarılı
```

### 8.2 SQL Injection Koruması

**Güvenli Parametre Kullanımı:**

```python
# Güvenli
sql = text("SELECT * FROM personel WHERE kullanici_adi = :user")
result = conn.execute(sql, {"user": username})

# Güvensiz (KULLANMAYIN!)
sql = f"SELECT * FROM personel WHERE kullanici_adi = '{username}'"
```

### 8.3 Session Yönetimi

**Session Timeout:**

```python
# config.toml
[server]
sessionTimeout = 1800  # 30 dakika
```

**Çıkış Yönetimi:**

```python
if st.button("Çıkış Yap"):
    st.session_state.logged_in = False
    st.session_state.clear()  # Tüm session'ı temizle
    st.rerun()
```

---

## 📞 Geliştirici Desteği

**Teknik Sorular:**
- GitHub Issues: [github.com/emrecavdar83/EKLER-STAN_QMS/issues](https://github.com/emrecavdar83/EKLER-STAN_QMS/issues)

**Katkıda Bulunma:**
- Pull Request açın
- Kod standartlarına uyun (PEP 8)
- Test senaryoları ekleyin

---

**Son Güncelleme:** 22 Ocak 2026  
**Versiyon:** 1.0
