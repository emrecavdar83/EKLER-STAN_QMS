-- =============================================
-- FAZ 5.5: DEPARTMAN HİYERARŞİSİ MİGRASYONU (DÜZELTİLMİŞ)
-- =============================================

-- 0. ÖNCE PRIMARY KEY GARANTİSİ (Hata 42830 Çözümü)
-- Eğer tablo pandas ile oluşturulduysa PK tanımı eksik olabilir.
DO $$ 
BEGIN 
    -- Eğer constraint yoksa ekle
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ayarlar_bolumler_pkey') THEN
        ALTER TABLE ayarlar_bolumler ADD PRIMARY KEY (id);
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        -- id sütunu unique olmayabilir veya null olabilir, bu durumda hata verir.
        -- Bu durumda önce temizlik gerekebilir ama şimdilik PK eklemeyi deniyoruz.
        RAISE NOTICE 'Primary Key eklenirken hata veya zaten var: %', SQLERRM;
END $$;

-- 1. 'ana_departman_id' sütunu ekle (Self-Reference)
ALTER TABLE ayarlar_bolumler ADD COLUMN IF NOT EXISTS ana_departman_id INTEGER REFERENCES ayarlar_bolumler(id) ON DELETE SET NULL;

-- 2. Hızlı sorgulama için index
CREATE INDEX IF NOT EXISTS idx_departman_parent ON ayarlar_bolumler(ana_departman_id);
