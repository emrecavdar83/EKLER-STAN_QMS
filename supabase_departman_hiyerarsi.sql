-- =============================================
-- FAZ 5.5: DEPARTMAN HİYERARŞİSİ MİGRASYONU
-- =============================================

-- 1. 'ana_departman_id' sütunu ekle (Self-Reference)
ALTER TABLE ayarlar_bolumler ADD COLUMN IF NOT EXISTS ana_departman_id INTEGER REFERENCES ayarlar_bolumler(id) ON DELETE SET NULL;

-- 2. Hızlı sorgulama için index
CREATE INDEX IF NOT EXISTS idx_departman_parent ON ayarlar_bolumler(ana_departman_id);

-- 3. Örnek Veri (Opsiyonel - Sadece fikir vermesi için)
-- INSERT INTO ayarlar_bolumler (bolum_adi, ana_departman_id, sira_no) VALUES ('Bulaşıkhane', (SELECT id FROM ayarlar_bolumler WHERE bolum_adi='ÜRETİM' LIMIT 1), 15);
