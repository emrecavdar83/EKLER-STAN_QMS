-- =============================================
-- FAZ 5: BÜYÜK ENTEGRASYON MİGRASYONU
-- =============================================
-- Bu scripti Supabase 'SQL Editor' kısmında çalıştırın.

-- 1. Lokasyonlar tablosuna 'Sorumlu Departman' ekle
ALTER TABLE lokasyonlar ADD COLUMN IF NOT EXISTS sorumlu_departman TEXT;

-- 2. Lokasyon Tip kısıtlamasını güncelle (HAT ekle)
-- Mevcut constraint'i güvenli şekilde kaldırıp yenisini ekliyoruz
ALTER TABLE lokasyonlar DROP CONSTRAINT IF EXISTS lokasyonlar_tip_check;
ALTER TABLE lokasyonlar ADD CONSTRAINT lokasyonlar_tip_check CHECK (tip IN ('Kat', 'Bölüm', 'Hat', 'Ekipman'));

-- 3. Vekaletler tablosunu oluştur
CREATE TABLE IF NOT EXISTS vekaletler (
    id SERIAL PRIMARY KEY,
    veren_kullanici TEXT NOT NULL, -- Kullanıcı Adı
    alan_kullanici TEXT NOT NULL,  -- Kullanıcı Adı (Vekil)
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Hızlı sorgulama için indexler
CREATE INDEX IF NOT EXISTS idx_vekalet_veren ON vekaletler(veren_kullanici);
CREATE INDEX IF NOT EXISTS idx_vekalet_alan ON vekaletler(alan_kullanici);
CREATE INDEX IF NOT EXISTS idx_lokasyon_sorumlu ON lokasyonlar(sorumlu_departman);

-- 4. Örnek: Mevcut lokasyonları varsayılan departmana atama (Opsiyonel)
-- UPDATE lokasyonlar SET sorumlu_departman = 'Üretim' WHERE sorumlu_departman IS NULL;
