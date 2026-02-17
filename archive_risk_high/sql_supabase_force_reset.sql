-- BAĞIMLILIKLARI AŞARAK TABLOLARI SİLME KOMUTU
-- Bu komutu Supabase SQL Editor'da çalıştırın

-- 1. Önce bağımlı olan 'lokasyon_proses_atama' tablosunu sil (eğer varsa)
DROP TABLE IF EXISTS lokasyon_proses_atama CASCADE;

-- 2. Sonra 'lokasyonlar' tablosunu sil
DROP TABLE IF EXISTS lokasyonlar CASCADE;

-- 3. Proses tiplerini de silmek isterseniz (opsiyonel)
-- DROP TABLE IF EXISTS proses_tipleri CASCADE;

-- ---------------------------------------------------------
-- ŞİMDİ TABLOLARI TEKRAR OLUŞTURUN (Aşağıdaki kodu da çalıştırın)
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS lokasyonlar (
    id SERIAL PRIMARY KEY,
    ad TEXT NOT NULL,
    tip TEXT CHECK (tip IN ('Kat', 'Bölüm', 'Ekipman')),
    parent_id INTEGER REFERENCES lokasyonlar(id) ON DELETE SET NULL,
    sorumlu_id INTEGER,
    sira_no INTEGER DEFAULT 0,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lokasyon_proses_atama (
    id SERIAL PRIMARY KEY,
    lokasyon_id INTEGER REFERENCES lokasyonlar(id) ON DELETE CASCADE,
    proses_tipi_id INTEGER REFERENCES proses_tipleri(id) ON DELETE CASCADE,
    siklik TEXT CHECK (siklik IN ('Her Kullanım', 'Günlük', 'Haftalık', 'Aylık', '3 Aylık', 'Yıllık')),
    sorumlu_id INTEGER,
    notlar TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(lokasyon_id, proses_tipi_id)
);
