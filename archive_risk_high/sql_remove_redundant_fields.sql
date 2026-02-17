-- ============================================
-- Personel Şeması Temizleme Migration Script
-- ============================================
-- Amaç: Gereksiz sütunları (bolum, sorumlu_bolum) kaldırmak
-- Tarih: 2026-01-20
-- ============================================

-- ADIM 1: YEDEK AL (ÖNEMLİ!)
-- ============================================
CREATE TABLE IF NOT EXISTS personel_backup_20260120 AS 
SELECT * FROM personel;

-- Yedek alındığını doğrula
SELECT COUNT(*) as yedek_kayit_sayisi FROM personel_backup_20260120;


-- ADIM 2: VERİ KONTROLÜ
-- ============================================
-- sorumlu_bolum kullanımını kontrol et
SELECT 
    'sorumlu_bolum' as alan,
    COUNT(*) as toplam,
    COUNT(CASE WHEN sorumlu_bolum IS NOT NULL AND sorumlu_bolum != '' THEN 1 END) as dolu_kayit
FROM personel;

-- bolum kullanımını kontrol et
SELECT 
    'bolum' as alan,
    COUNT(*) as toplam,
    COUNT(CASE WHEN bolum IS NOT NULL AND bolum != '' THEN 1 END) as dolu_kayit,
    COUNT(CASE WHEN departman_id IS NOT NULL THEN 1 END) as departman_id_dolu
FROM personel;


-- ADIM 3: SON VERİ MİGRASYONU (Eğer gerekirse)
-- ============================================
-- Eğer hala bolum değeri olup departman_id boş olan kayıtlar varsa:
UPDATE personel p
SET departman_id = (
    SELECT id FROM ayarlar_bolumler 
    WHERE LOWER(bolum_adi) = LOWER(p.bolum)
    LIMIT 1
)
WHERE departman_id IS NULL 
  AND bolum IS NOT NULL 
  AND bolum != '';

-- Kaç kayıt güncellendi kontrol et
SELECT COUNT(*) as guncellenen_kayit
FROM personel
WHERE departman_id IS NOT NULL AND bolum IS NOT NULL;


-- ADIM 4: SÜTUNLARI KALDIR
-- ============================================
-- ⚠️ DİKKAT: Bu adımı çalıştırmadan önce:
-- 1. Uygulama kodunun güncellendiğinden emin olun
-- 2. Streamlit Cloud'da deploy tamamlanmış olsun
-- 3. Tüm testler başarılı olsun

-- sorumlu_bolum sütununu kaldır
ALTER TABLE personel DROP COLUMN IF EXISTS sorumlu_bolum;

-- bolum sütununu kaldır
ALTER TABLE personel DROP COLUMN IF EXISTS bolum;


-- ADIM 5: DOĞRULAMA
-- ============================================
-- Sütunların kaldırıldığını doğrula
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'personel'
ORDER BY ordinal_position;

-- Tüm personelin departman_id'si olduğunu doğrula
SELECT 
    COUNT(*) as toplam_personel,
    COUNT(departman_id) as departman_id_olan,
    COUNT(*) - COUNT(departman_id) as departman_id_olmayan
FROM personel;


-- ============================================
-- GERİ ALMA SCRIPT'İ (Acil Durum İçin)
-- ============================================
-- Eğer bir sorun olursa ve geri almak isterseniz:

/*
-- Sütunları geri ekle
ALTER TABLE personel ADD COLUMN bolum TEXT;
ALTER TABLE personel ADD COLUMN sorumlu_bolum TEXT;

-- Yedekten verileri geri yükle
UPDATE personel p
SET 
    bolum = b.bolum,
    sorumlu_bolum = b.sorumlu_bolum
FROM personel_backup_20260120 b
WHERE p.id = b.id;

-- Doğrula
SELECT COUNT(*) FROM personel WHERE bolum IS NOT NULL;
*/


-- ============================================
-- TEMİZLİK (Migration başarılı olduktan sonra)
-- ============================================
-- Yedek tablosunu kaldır (isteğe bağlı, 1 hafta sonra)
-- DROP TABLE IF EXISTS personel_backup_20260120;
