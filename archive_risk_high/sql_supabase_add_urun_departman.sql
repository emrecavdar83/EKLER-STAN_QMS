-- =====================================================
-- ÜRÜN - DEPARTMAN EŞLEŞTİRME MİGRASYONU
-- =====================================================
-- Amaç: Mevcut ürün listesini BOZMADAN, her ürüne
-- opsiyonel olarak bir 'Sorumlu Departman' atayabilmek.
-- =====================================================

DO $$ 
BEGIN
    -- 'sorumlu_departman' sütunu yoksa ekle
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ayarlar_urunler' AND column_name = 'sorumlu_departman'
    ) THEN
        ALTER TABLE ayarlar_urunler ADD COLUMN sorumlu_departman TEXT;
    END IF;
END $$;

-- Not: Mevcut veriler silinmez, sorumlu_departman başlangıçta NULL olur.
