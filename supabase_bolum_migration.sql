-- =====================================================
-- BÖLÜM YÖNETİMİ MİGRASYON SCRIPTI (SUPABASE/POSTGRESQL)
-- =====================================================
-- Bu script Supabase SQL Editor'de çalıştırılmalıdır
-- =====================================================

-- 1. ayarlar_bolumler tablosunu oluştur
CREATE TABLE IF NOT EXISTS ayarlar_bolumler (
    id SERIAL PRIMARY KEY,
    bolum_adi TEXT NOT NULL UNIQUE,
    aktif INTEGER DEFAULT 1,
    sira_no INTEGER DEFAULT 0,
    aciklama TEXT
);

-- 2. Varsayılan bölümleri ekle (eğer tablo boşsa)
INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'PATAŞU', 1, 1, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'PATAŞU');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'KEK', 1, 2, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'KEK');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'KREMA', 1, 3, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'KREMA');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'PROFİTEROL', 1, 4, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'PROFİTEROL');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'RULO PASTA', 1, 5, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'RULO PASTA');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'BOMBA', 1, 6, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'BOMBA');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'TEMİZLİK', 1, 7, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'TEMİZLİK');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'BULAŞIK', 1, 8, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'BULAŞIK');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'DEPO', 1, 9, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'DEPO');

-- 3. Mevcut personel kayıtlarındaki bölümleri ekle
INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT DISTINCT bolum, 1, 100, 'Mevcut kayıtlardan alındı'
FROM personel
WHERE bolum IS NOT NULL 
  AND bolum != ''
  AND NOT EXISTS (
    SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = personel.bolum
  );

-- 4. Kontrol sorgusu (opsiyonel - sonuçları görmek için)
SELECT 
    COUNT(*) as toplam_bolum,
    SUM(CASE WHEN aktif = 1 THEN 1 ELSE 0 END) as aktif_bolum
FROM ayarlar_bolumler;

-- 5. Bölüm listesini göster
SELECT bolum_adi, aktif, sira_no, aciklama
FROM ayarlar_bolumler
ORDER BY sira_no;

-- =====================================================
-- MİGRASYON TAMAMLANDI
-- =====================================================
-- Streamlit Cloud uygulamanızı yeniden başlatın (Reboot)
-- =====================================================
