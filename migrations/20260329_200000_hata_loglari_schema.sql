-- UP MIGRATION: Hata Günlüğü (AI-Friendly) Tablosu
-- Bu tablo sayesinde hatalar "Kara Kutu" (Black Box) mantığı ile izlenebilecektir.

-- 1. Hata Logları Tablosu
CREATE TABLE IF NOT EXISTS hata_loglari (
    id SERIAL PRIMARY KEY,
    hata_kodu VARCHAR(20) UNIQUE NOT NULL,      -- Örn: #E-20260329-102
    seviye VARCHAR(20) DEFAULT 'ERROR',         -- CRITICAL, ERROR, WARNING
    modul VARCHAR(50),                          -- Hangi modül (temizlik, map vb.)
    fonksiyon VARCHAR(100),                     -- Hangi fonksiyon/metot
    hata_mesaji TEXT NOT NULL,                  -- Python hata mesajı
    stack_trace TEXT,                           -- Detaylı traceback (Debug için)
    context_data TEXT,                          -- JSON: Hata anındaki değişkenlerin durumu
    ai_diagnosis TEXT,                          -- AI Tarafından eklenen kısa teşhis/çözüm önerisi
    kullanici_id INTEGER,                       -- Hata anındaki aktif kullanıcı
    is_fixed INTEGER DEFAULT 0,                 -- Çözüldü mü? (0: Hayır, 1: Evet)
    zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- Hata saati
);

-- SQLite Desteği (Local Develop için fallback PK/Timestamp)
-- Not: connection.py içindeki tablolama mantığı bu DDL'yi işleyecektir.

-- 2. İndeksleme (Hızlı Arama)
CREATE INDEX IF NOT EXISTS idx_hata_loglari_kodu ON hata_loglari(hata_kodu);
CREATE INDEX IF NOT EXISTS idx_hata_loglari_zaman ON hata_loglari(zaman);
CREATE INDEX IF NOT EXISTS idx_hata_loglari_fixed ON hata_loglari(is_fixed);

-- DOWN MIGRATION
-- DROP TABLE IF EXISTS hata_loglari;
