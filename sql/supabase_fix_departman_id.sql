-- =============================================
-- ID SÜTUNU OTO-ARTAN (AUTO-INCREMENT) ONARIMI
-- Hata: null value in column "id" violates not-null constraint
-- =============================================

-- 1. Sequence oluştur (Eğer yoksa)
CREATE SEQUENCE IF NOT EXISTS ayarlar_bolumler_id_seq;

-- 2. Sequence'i tablodaki mevcut en büyük ID'ye eşitle (Çakışma olmasın)
-- Tablo boşsa 1'den başlar.
SELECT setval('ayarlar_bolumler_id_seq', COALESCE((SELECT MAX(id) FROM ayarlar_bolumler), 0) + 1, false);

-- 3. 'id' sütununa varsayılan değer olarak bu sequence'i ata
ALTER TABLE ayarlar_bolumler ALTER COLUMN id SET DEFAULT nextval('ayarlar_bolumler_id_seq');

-- 4. 'id' sütununun boş olamayacağını garanti et
ALTER TABLE ayarlar_bolumler ALTER COLUMN id SET NOT NULL;

-- 5. Primary Key olduğundan emin ol (Önceki adımda yapılmadıysa)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ayarlar_bolumler_pkey') THEN
        ALTER TABLE ayarlar_bolumler ADD PRIMARY KEY (id);
    END IF;
END $$;
