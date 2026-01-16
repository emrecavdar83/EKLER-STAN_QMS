-- Temizlik Bölümleri (Hiyerarşik) Tablo Düzeltmesi
-- Supabase'de çalıştırılacak

-- Önce mevcut tabloyu kontrol et
-- SELECT * FROM tanim_bolumler;

-- Eğer tablo yoksa veya yapısı yanlışsa, doğru şekilde oluştur
CREATE TABLE IF NOT EXISTS tanim_bolumler (
    id SERIAL PRIMARY KEY,
    bolum_adi TEXT NOT NULL,
    parent_id INTEGER REFERENCES tanim_bolumler(id) ON DELETE SET NULL
);

-- Varsayılan bölümleri ekle (eğer boşsa)
INSERT INTO tanim_bolumler (bolum_adi, parent_id) 
SELECT 'PATAŞU', NULL WHERE NOT EXISTS (SELECT 1 FROM tanim_bolumler WHERE bolum_adi = 'PATAŞU');

INSERT INTO tanim_bolumler (bolum_adi, parent_id) 
SELECT 'KEK', NULL WHERE NOT EXISTS (SELECT 1 FROM tanim_bolumler WHERE bolum_adi = 'KEK');

INSERT INTO tanim_bolumler (bolum_adi, parent_id) 
SELECT 'KREMA', NULL WHERE NOT EXISTS (SELECT 1 FROM tanim_bolumler WHERE bolum_adi = 'KREMA');

INSERT INTO tanim_bolumler (bolum_adi, parent_id) 
SELECT 'PROFİTEROL', NULL WHERE NOT EXISTS (SELECT 1 FROM tanim_bolumler WHERE bolum_adi = 'PROFİTEROL');

INSERT INTO tanim_bolumler (bolum_adi, parent_id) 
SELECT 'BOMBA', NULL WHERE NOT EXISTS (SELECT 1 FROM tanim_bolumler WHERE bolum_adi = 'BOMBA');

INSERT INTO tanim_bolumler (bolum_adi, parent_id) 
SELECT 'DEPO', NULL WHERE NOT EXISTS (SELECT 1 FROM tanim_bolumler WHERE bolum_adi = 'DEPO');

-- Ekipmanlar tablosu
CREATE TABLE IF NOT EXISTS tanim_ekipmanlar (
    id SERIAL PRIMARY KEY,
    ekipman_adi TEXT NOT NULL,
    bagli_bolum TEXT
);

-- Metotlar tablosu  
CREATE TABLE IF NOT EXISTS tanim_metotlar (
    id SERIAL PRIMARY KEY,
    metot_adi TEXT NOT NULL,
    aciklama TEXT
);

-- Doğrulama
SELECT * FROM tanim_bolumler ORDER BY id;
