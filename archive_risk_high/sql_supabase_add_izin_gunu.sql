-- =====================================================
-- PERSONEL TABLOSUNA İZİN GÜNÜ KOLONU EKLEME
-- =====================================================
-- Supabase SQL Editor'de çalıştırın
-- =====================================================

-- izin_gunu kolonunu ekle (yoksa)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'personel' AND column_name = 'izin_gunu'
    ) THEN
        ALTER TABLE personel ADD COLUMN izin_gunu TEXT;
        -- Varsayılan olarak boş bırak veya "-" koy
        UPDATE personel SET izin_gunu = '-' WHERE izin_gunu IS NULL;
    END IF;
END $$;

-- Kontrol: Personel tablosu kolonlarını göster
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'personel'
ORDER BY ordinal_position;

-- Kontrol: İlk 5 personel kaydını göster
SELECT ad_soyad, bolum, vardiya, izin_gunu 
FROM personel 
LIMIT 5;

-- =====================================================
-- MİGRASYON TAMAMLANDI
-- =====================================================
