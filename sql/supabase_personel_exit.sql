-- PERSONEL İŞTEN ÇIKIŞ SÜRECİ MIGRATION
-- Bu komutları Supabase SQL Editor'de çalıştırın

-- 1. Yeni Kolonları Ekle (Eğer yoksa)
ALTER TABLE personel ADD COLUMN IF NOT EXISTS is_cikis_tarihi DATE;
ALTER TABLE personel ADD COLUMN IF NOT EXISTS ayrilma_sebebi TEXT;

-- 2. Mevcut Boş Durumları 'AKTİF' Yap (Data Cleaning)
UPDATE personel 
SET durum = 'AKTİF' 
WHERE durum IS NULL OR durum = '';

-- 3. Kontrol Sorgusu
SELECT ad_soyad, durum, is_cikis_tarihi, ayrilma_sebebi 
FROM personel 
LIMIT 5;
