-- ==========================================
-- EKLERİSTAN QMS - SUPABASE FULL SETUP & OPTIMIZATION (v2)
-- ==========================================
-- Bu script TÜM tabloları (Eksik tablo hatası verenler dahil) oluşturur ve sistemi hızlandırır.
-- Supabase SQL Editor'e yapıştırıp "Run" butonuna basınız.

-- 1. TEMEL AYAR TABLOLARI
CREATE TABLE IF NOT EXISTS personel (
    id SERIAL PRIMARY KEY,
    ad_soyad TEXT, kullanici_adi TEXT, sifre TEXT, rol TEXT, bolum TEXT,
    gorev TEXT, vardiya TEXT, durum TEXT DEFAULT 'AKTİF', 
    ise_giris_tarihi TEXT, sorumlu_bolum TEXT
);

CREATE TABLE IF NOT EXISTS ayarlar_urunler (
    id SERIAL PRIMARY KEY,
    urun_adi TEXT, raf_omru_gun INTEGER, numune_sayisi INTEGER DEFAULT 3, 
    gramaj REAL, kod TEXT,
    olcum1_ad TEXT, olcum1_min REAL, olcum1_max REAL,
    olcum2_ad TEXT, olcum2_min REAL, olcum2_max REAL,
    olcum3_ad TEXT, olcum3_min REAL, olcum3_max REAL,
    olcum_sikligi_dk REAL, uretim_bolumu TEXT
);

CREATE TABLE IF NOT EXISTS urun_parametreleri (
    id SERIAL PRIMARY KEY,
    urun_adi TEXT, parametre_adi TEXT, min_deger REAL, max_deger REAL
);

-- 2. KAYIT TABLOLARI (URETIM, KALITE, HIJYEN, TEMIZLIK)
CREATE TABLE IF NOT EXISTS depo_giris_kayitlari (
    id SERIAL PRIMARY KEY,
    tarih TEXT, vardiya TEXT, kullanici TEXT, islem_tipi TEXT,
    urun TEXT, lot_no TEXT, miktar INTEGER, fire INTEGER,
    notlar TEXT, zaman_damgasi TEXT
);

CREATE TABLE IF NOT EXISTS urun_kpi_kontrol (
    id SERIAL PRIMARY KEY,
    tarih TEXT, saat TEXT, vardiya TEXT, urun TEXT, lot_no TEXT,
    stt TEXT, numune_no TEXT, olcum1 REAL, olcum2 REAL, olcum3 REAL,
    karar TEXT, kullanici TEXT, tat TEXT, goruntu TEXT, notlar TEXT
);

CREATE TABLE IF NOT EXISTS hijyen_kontrol_kayitlari (
    id SERIAL PRIMARY KEY,
    tarih TEXT, saat TEXT, kullanici TEXT, vardiya TEXT,
    bolum TEXT, personel TEXT, durum TEXT, sebep TEXT, aksiyon TEXT
);

CREATE TABLE IF NOT EXISTS temizlik_kayitlari (
    id SERIAL PRIMARY KEY,
    tarih TEXT, saat TEXT, kullanici TEXT, bolum TEXT,
    islem TEXT, durum TEXT, aciklama TEXT
);

-- 3. TANIMLAMALAR, KIMYASALLAR VE GMP
CREATE TABLE IF NOT EXISTS tanim_bolumler (
    id SERIAL PRIMARY KEY, bolum_adi TEXT, parent_id INTEGER
);

CREATE TABLE IF NOT EXISTS tanim_ekipmanlar (
    id SERIAL PRIMARY KEY, ekipman_adi TEXT, bagli_bolum TEXT
);

CREATE TABLE IF NOT EXISTS tanim_metotlar (
    id SERIAL PRIMARY KEY, metot_adi TEXT, aciklama TEXT
);

CREATE TABLE IF NOT EXISTS kimyasal_envanter (
    id SERIAL PRIMARY KEY, kimyasal_adi TEXT, tedarikci TEXT, 
    msds_yolu TEXT, tds_yolu TEXT
);

CREATE TABLE IF NOT EXISTS ayarlar_temizlik_plani (
    id SERIAL PRIMARY KEY, kat_bolum TEXT, yer_ekipman TEXT, risk TEXT, 
    siklik TEXT, kimyasal TEXT, uygulama_yontemi TEXT, validasyon TEXT, 
    uygulayici TEXT, kontrol_eden TEXT, kayit_no TEXT, 
    validasyon_siklik TEXT, verifikasyon TEXT, verifikasyon_siklik TEXT
);

CREATE TABLE IF NOT EXISTS gmp_soru_havuzu (
    id SERIAL PRIMARY KEY, kategori TEXT NOT NULL, soru_metni TEXT NOT NULL,
    risk_puani INTEGER DEFAULT 1, brc_ref TEXT, frekans TEXT DEFAULT 'GÜNLÜK',
    aktif BOOLEAN DEFAULT TRUE, lokasyon_ids TEXT
);

CREATE TABLE IF NOT EXISTS gmp_denetim_kayitlari (
    id SERIAL PRIMARY KEY, tarih DATE NOT NULL, saat TEXT, kullanici TEXT NOT NULL,
    lokasyon_id INTEGER, soru_id INTEGER, durum TEXT NOT NULL, 
    fotograf_yolu TEXT, notlar TEXT, brc_ref TEXT, risk_puani INTEGER
);

-- 4. YETKI VE ROLLÜ SİSTEM
CREATE TABLE IF NOT EXISTS ayarlar_roller (
    id SERIAL PRIMARY KEY, rol_adi TEXT UNIQUE, aciklama TEXT, 
    aktif BOOLEAN DEFAULT TRUE, olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ayarlar_yetkiler (
    id SERIAL PRIMARY KEY, rol_adi TEXT, modul_adi TEXT, 
    erisim_turu TEXT, -- 'Yok', 'Görüntüle', 'Düzenle'
    FOREIGN KEY (rol_adi) REFERENCES ayarlar_roller(rol_adi)
);

-- 5. HIZ OPTİMİZASYON İNDEKSLERİ (YILDIRIM HIZI İÇİN)
CREATE INDEX IF NOT EXISTS idx_personel_user ON personel(kullanici_adi);
CREATE INDEX IF NOT EXISTS idx_gmp_soru_aktif ON gmp_soru_havuzu(aktif, frekans);
CREATE INDEX IF NOT EXISTS idx_depo_tarih ON depo_giris_kayitlari(tarih);
CREATE INDEX IF NOT EXISTS idx_kpi_lot ON urun_kpi_kontrol(lot_no);
CREATE INDEX IF NOT EXISTS idx_hijyen_tarih ON hijyen_kontrol_kayitlari(tarih);
CREATE INDEX IF NOT EXISTS idx_temizlik_tarih ON temizlik_kayitlari(tarih);

-- BAŞARI MESAJI
-- SELECT 'Sistem v2 başarıyla optimize edildi ve TÜM eksik tablolar oluşturuldu.' as sonuc;
