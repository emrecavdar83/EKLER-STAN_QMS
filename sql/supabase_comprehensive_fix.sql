-- EKLERİSTAN QMS - Kapsamlı Veritabanı Hizalama Sorgusu
-- Bu scripti Supabase SQL Editor üzerinden çalıştırın.

-- 1. EKSİK TABLOLARI OLUŞTUR
CREATE TABLE IF NOT EXISTS ayarlar_bolumler (
    id SERIAL PRIMARY KEY,
    bolum_adi TEXT NOT NULL UNIQUE,
    aktif BOOLEAN DEFAULT TRUE,
    sira_no INTEGER DEFAULT 0,
    aciklama TEXT,
    ana_departman_id INTEGER
);

CREATE TABLE IF NOT EXISTS ayarlar_yetkiler (
    id SERIAL PRIMARY KEY,
    rol_adi TEXT NOT NULL,
    modul_adi TEXT NOT NULL,
    erisim_turu TEXT NOT NULL -- 'Yok', 'Görüntüle', 'Düzenle'
);

CREATE TABLE IF NOT EXISTS personel (
    id SERIAL PRIMARY KEY,
    ad_soyad TEXT,
    bolum TEXT,
    gorev TEXT,
    vardiya TEXT,
    durum TEXT DEFAULT 'AKTİF',
    kullanici_adi TEXT,
    sifre TEXT,
    rol TEXT,
    sorumlu_bolum TEXT,
    departman_id INTEGER REFERENCES ayarlar_bolumler(id),
    yonetici_id INTEGER REFERENCES personel(id),
    pozisyon_seviye INTEGER DEFAULT 5,
    ise_giris_tarihi DATE,
    kat TEXT,
    izin_gunu TEXT,
    is_cikis_tarihi DATE,
    ayrilma_sebebi TEXT
);

CREATE TABLE IF NOT EXISTS personel_vardiya_programi (
    id SERIAL PRIMARY KEY,
    personel_id INTEGER REFERENCES personel(id) ON DELETE CASCADE,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    vardiya TEXT NOT NULL,
    izin_gunleri TEXT,
    aciklama TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ayarlar_temizlik_plani (
    id SERIAL PRIMARY KEY,
    kat_bolum TEXT,
    yer_ekipman TEXT,
    risk TEXT,
    siklik TEXT,
    kimyasal TEXT,
    uygulama_yontemi TEXT,
    validasyon TEXT,
    uygulayici TEXT,
    kontrol_eden TEXT,
    kayit_no TEXT,
    validasyon_siklik TEXT,
    verifikasyon TEXT,
    verifikasyon_siklik TEXT,
    kat TEXT
);

CREATE TABLE IF NOT EXISTS lokasyonlar (
    id SERIAL PRIMARY KEY,
    ad TEXT NOT NULL,
    tip TEXT,
    parent_id INTEGER REFERENCES lokasyonlar(id),
    sorumlu_id INTEGER REFERENCES personel(id),
    sira_no INTEGER DEFAULT 0,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proses_tipleri (
    id SERIAL PRIMARY KEY,
    ad TEXT NOT NULL,
    aciklama TEXT
);

CREATE TABLE IF NOT EXISTS lokasyon_proses_atama (
    id SERIAL PRIMARY KEY,
    lokasyon_id INTEGER REFERENCES lokasyonlar(id) ON DELETE CASCADE,
    proses_tipi_id INTEGER REFERENCES proses_tipleri(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tanim_metotlar (
    id SERIAL PRIMARY KEY,
    metot_adi TEXT NOT NULL,
    aciklama TEXT
);

CREATE TABLE IF NOT EXISTS kimyasal_envanter (
    id SERIAL PRIMARY KEY,
    kimyasal_adi TEXT NOT NULL,
    tedarikci TEXT,
    kullanim_alani TEXT,
    msds_link TEXT,
    tds_link TEXT,
    onay_durumu TEXT
);

CREATE TABLE IF NOT EXISTS gmp_soru_havuzu (
    id SERIAL PRIMARY KEY,
    kategori TEXT NOT NULL,
    soru_metni TEXT NOT NULL,
    risk_puani INTEGER DEFAULT 1,
    brc_ref TEXT,
    frekans TEXT DEFAULT 'GÜNLÜK',
    aktif BOOLEAN DEFAULT TRUE,
    lokasyon_ids TEXT
);

CREATE TABLE IF NOT EXISTS ayarlar_urunler (
    id SERIAL PRIMARY KEY,
    urun_adi TEXT,
    raf_omru_gun INTEGER,
    numune_sayisi INTEGER,
    gramaj REAL,
    kod TEXT,
    olcum1_ad TEXT, olcum1_min REAL, olcum1_max REAL,
    olcum2_ad TEXT, olcum2_min REAL, olcum2_max REAL,
    olcum3_ad TEXT, olcum3_min REAL, olcum3_max REAL,
    olcum_sikligi_dk REAL,
    uretim_bolumu TEXT,
    sorumlu_departman TEXT
);

-- 2. MEVCUT TABLOLARA EKSİK KOLONLARI EKLE
ALTER TABLE personel ADD COLUMN IF NOT EXISTS is_cikis_tarihi DATE;
ALTER TABLE personel ADD COLUMN IF NOT EXISTS ayrilma_sebebi TEXT;
ALTER TABLE personel ADD COLUMN IF NOT EXISTS kat TEXT;
ALTER TABLE personel ADD COLUMN IF NOT EXISTS izin_gunu TEXT;

-- 3. VIEW GÜNCELLEME
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
