-- =====================================================
-- BÖLÜM YÖNETİMİ MİGRASYON SCRIPTI (SUPABASE/POSTGRESQL)
-- =====================================================
-- Bu script Supabase SQL Editor'de çalıştırılmalıdır
-- MEVCUT TABLO VARSA EKSİK KOLONLARI EKLER
-- =====================================================

-- 1. Önce tabloyu oluştur (yoksa)
CREATE TABLE IF NOT EXISTS ayarlar_bolumler (
    id SERIAL PRIMARY KEY,
    bolum_adi TEXT NOT NULL UNIQUE
);

-- 2. Eksik kolonları ekle (tablo zaten varsa)
-- aktif kolonu
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ayarlar_bolumler' AND column_name = 'aktif'
    ) THEN
        ALTER TABLE ayarlar_bolumler ADD COLUMN aktif BOOLEAN DEFAULT TRUE;
        UPDATE ayarlar_bolumler SET aktif = TRUE WHERE aktif IS NULL;
    END IF;
END $$;

-- sira_no kolonu
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ayarlar_bolumler' AND column_name = 'sira_no'
    ) THEN
        ALTER TABLE ayarlar_bolumler ADD COLUMN sira_no INTEGER DEFAULT 0;
        UPDATE ayarlar_bolumler SET sira_no = 0 WHERE sira_no IS NULL;
    END IF;
END $$;

-- aciklama kolonu
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ayarlar_bolumler' AND column_name = 'aciklama'
    ) THEN
        ALTER TABLE ayarlar_bolumler ADD COLUMN aciklama TEXT;
    END IF;
END $$;

-- 3. Varsayılan bölümleri ekle (yoksa)
INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'PATAŞU', TRUE, 1, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'PATAŞU');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'KEK', TRUE, 2, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'KEK');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'KREMA', TRUE, 3, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'KREMA');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'PROFİTEROL', TRUE, 4, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'PROFİTEROL');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'RULO PASTA', TRUE, 5, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'RULO PASTA');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'BOMBA', TRUE, 6, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'BOMBA');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'TEMİZLİK', TRUE, 7, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'TEMİZLİK');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'BULAŞIK', TRUE, 8, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'BULAŞIK');

INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'DEPO', TRUE, 9, 'Üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'DEPO');

-- 4. Mevcut personel kayıtlarındaki bölümleri ekle
INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT DISTINCT bolum, TRUE, 100, 'Mevcut kayıtlardan alındı'
FROM personel
WHERE bolum IS NOT NULL 
  AND bolum != ''
  AND NOT EXISTS (
    SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = personel.bolum
  );

-- 5. Mevcut kayıtların sira_no değerlerini güncelle (eğer 0 ise)
UPDATE ayarlar_bolumler 
SET sira_no = CASE bolum_adi
    WHEN 'PATAŞU' THEN 1
    WHEN 'KEK' THEN 2
    WHEN 'KREMA' THEN 3
    WHEN 'PROFİTEROL' THEN 4
    WHEN 'RULO PASTA' THEN 5
    WHEN 'BOMBA' THEN 6
    WHEN 'TEMİZLİK' THEN 7
    WHEN 'BULAŞIK' THEN 8
    WHEN 'DEPO' THEN 9
    ELSE sira_no
END
WHERE sira_no = 0;

-- 6. Kontrol sorgusu (sonuçları görmek için)
SELECT 
    COUNT(*) as toplam_bolum,
    SUM(CASE WHEN aktif = TRUE THEN 1 ELSE 0 END) as aktif_bolum
FROM ayarlar_bolumler;

-- 7. Bölüm listesini göster
SELECT bolum_adi, aktif, sira_no, aciklama
FROM ayarlar_bolumler
ORDER BY sira_no;

-- =====================================================
-- MİGRASYON TAMAMLANDI
-- =====================================================
-- Streamlit Cloud uygulamanızı yeniden başlatın (Reboot)
-- =====================================================
