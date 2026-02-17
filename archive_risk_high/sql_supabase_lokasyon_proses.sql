-- Ekleristan QMS - Lokasyon ve Proses Yönetim Sistemi
-- Supabase'de çalıştırılacak SQL

-- =============================================
-- FAZ 1: LOKASYON HİYERARŞİSİ (KAT-BÖLÜM-EKİPMAN)
-- =============================================

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

-- Index for faster parent queries
CREATE INDEX IF NOT EXISTS idx_lokasyonlar_parent ON lokasyonlar(parent_id);
CREATE INDEX IF NOT EXISTS idx_lokasyonlar_tip ON lokasyonlar(tip);

-- =============================================
-- FAZ 2: MODÜLER PROSES TİPLERİ
-- =============================================

CREATE TABLE IF NOT EXISTS proses_tipleri (
    id SERIAL PRIMARY KEY,
    kod TEXT UNIQUE NOT NULL,        -- 'TEMIZLIK', 'KPI', 'URETIM'
    ad TEXT NOT NULL,                -- 'Temizlik Kontrolü'
    ikon TEXT,                       -- '🧹'
    modul_adi TEXT,                  -- İlgili modül adı
    aciklama TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Varsayılan prosesler
INSERT INTO proses_tipleri (kod, ad, ikon, modul_adi, aciklama) VALUES
('TEMIZLIK', 'Temizlik Kontrolü', '🧹', 'Temizlik Kontrol', 'Günlük/haftalık temizlik takibi'),
('KPI', 'KPI & Kalite Kontrol', '🍩', 'KPI Kontrol', 'Ürün kalite parametreleri ölçümü'),
('URETIM', 'Üretim Takibi', '🏭', 'Üretim Girişi', 'Üretim miktarları ve lot takibi'),
('GMP', 'GMP Denetimi', '🛡️', 'GMP Denetimi', 'Good Manufacturing Practice kontrolleri'),
('HIJYEN', 'Personel Hijyen', '🧼', 'Personel Hijyen', 'Personel hijyen kontrolleri')
ON CONFLICT (kod) DO NOTHING;

-- =============================================
-- FAZ 3: LOKASYON-PROSES ATAMA
-- =============================================

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

CREATE INDEX IF NOT EXISTS idx_lokasyon_proses_lokasyon ON lokasyon_proses_atama(lokasyon_id);
CREATE INDEX IF NOT EXISTS idx_lokasyon_proses_proses ON lokasyon_proses_atama(proses_tipi_id);

-- =============================================
-- ÖRNEK VERİLER (Fabrika Yapısı)
-- =============================================

-- Ana Katlar
INSERT INTO lokasyonlar (ad, tip, parent_id, sira_no) VALUES
('KAT 1 - ÜRETİM', 'Kat', NULL, 1),
('KAT 2 - PAKETLEME', 'Kat', NULL, 2),
('DEPO ALANI', 'Kat', NULL, 3)
ON CONFLICT DO NOTHING;

-- Bölümler (parent_id'ler sonra güncellenecek)
-- Not: Manuel olarak Kat ID'lerini belirlemeniz gerekebilir

-- =============================================
-- DOĞRULAMA
-- =============================================
SELECT 'Lokasyonlar' as tablo, COUNT(*) as kayit_sayisi FROM lokasyonlar
UNION ALL
SELECT 'Proses Tipleri', COUNT(*) FROM proses_tipleri
UNION ALL
SELECT 'Proses Atamaları', COUNT(*) FROM lokasyon_proses_atama;
