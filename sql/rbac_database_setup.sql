-- Dinamik Yetki Sistemi - Veritabanı Tabloları
-- Faz 1: Veritabanı Hazırlığı

-- 1. ROLLER TABLOSU
CREATE TABLE IF NOT EXISTS ayarlar_roller (
    id SERIAL PRIMARY KEY,
    rol_adi TEXT UNIQUE NOT NULL,
    aciklama TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    olusturma_tarihi TIMESTAMP DEFAULT NOW()
);

-- 2. BÖLÜMLER TABLOSU
CREATE TABLE IF NOT EXISTS ayarlar_bolumler (
    id SERIAL PRIMARY KEY,
    bolum_adi TEXT UNIQUE NOT NULL,
    aciklama TEXT,
    aktif BOOLEAN DEFAULT TRUE,
    olusturma_tarihi TIMESTAMP DEFAULT NOW()
);

-- 3. YETKİLER TABLOSU (Yetki Matrisi)
CREATE TABLE IF NOT EXISTS ayarlar_yetkiler (
    id SERIAL PRIMARY KEY,
    rol_adi TEXT NOT NULL,
    modul_adi TEXT NOT NULL,
    erisim_turu TEXT NOT NULL CHECK (erisim_turu IN ('Yok', 'Görüntüle', 'Düzenle')),
    UNIQUE(rol_adi, modul_adi),
    FOREIGN KEY (rol_adi) REFERENCES ayarlar_roller(rol_adi) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 4. MEVCUT ROLLERİ TABLOYA AKTAR
INSERT INTO ayarlar_roller (rol_adi, aciklama) VALUES
('Admin', 'Sistem yöneticisi - Tüm yetkilere sahip'),
('Kalite Sorumlusu', 'Kalite kontrol ve KPI yönetimi'),
('Vardiya Amiri', 'Vardiya operasyonları ve personel yönetimi'),
('Personel', 'Temel kullanıcı - Sınırlı erişim'),
('Depo Sorumlusu', 'Depo ve stok yönetimi')
ON CONFLICT (rol_adi) DO NOTHING;

-- 5. MEVCUT BÖLÜMLERİ TABLOYA AKTAR
INSERT INTO ayarlar_bolumler (bolum_adi, aciklama) VALUES
('Üretim', 'Üretim hattı ve imalat'),
('Paketleme', 'Ürün paketleme ve etiketleme'),
('Depo', 'Depo ve lojistik'),
('Ofis', 'İdari ve ofis personeli'),
('Kalite', 'Kalite kontrol laboratuvarı'),
('Yönetim', 'Üst yönetim'),
('Temizlik', 'Temizlik ve sanitasyon')
ON CONFLICT (bolum_adi) DO NOTHING;

-- 6. VARSAYILAN YETKİ MATRİSİ
-- Modüller: Üretim Girişi, KPI Kontrol, Personel Hijyen, Temizlik Kontrol, Raporlama, Ayarlar

-- Admin - Tüm yetkiler
INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES
('Admin', 'Üretim Girişi', 'Düzenle'),
('Admin', 'KPI Kontrol', 'Düzenle'),
('Admin', 'Personel Hijyen', 'Düzenle'),
('Admin', 'Temizlik Kontrol', 'Düzenle'),
('Admin', 'Raporlama', 'Düzenle'),
('Admin', 'Ayarlar', 'Düzenle')
ON CONFLICT (rol_adi, modul_adi) DO NOTHING;

-- Kalite Sorumlusu
INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES
('Kalite Sorumlusu', 'Üretim Girişi', 'Düzenle'),
('Kalite Sorumlusu', 'KPI Kontrol', 'Düzenle'),
('Kalite Sorumlusu', 'Personel Hijyen', 'Görüntüle'),
('Kalite Sorumlusu', 'Temizlik Kontrol', 'Görüntüle'),
('Kalite Sorumlusu', 'Raporlama', 'Görüntüle'),
('Kalite Sorumlusu', 'Ayarlar', 'Yok')
ON CONFLICT (rol_adi, modul_adi) DO NOTHING;

-- Vardiya Amiri
INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES
('Vardiya Amiri', 'Üretim Girişi', 'Düzenle'),
('Vardiya Amiri', 'KPI Kontrol', 'Görüntüle'),
('Vardiya Amiri', 'Personel Hijyen', 'Düzenle'),
('Vardiya Amiri', 'Temizlik Kontrol', 'Düzenle'),
('Vardiya Amiri', 'Raporlama', 'Yok'),
('Vardiya Amiri', 'Ayarlar', 'Yok')
ON CONFLICT (rol_adi, modul_adi) DO NOTHING;

-- Personel
INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES
('Personel', 'Üretim Girişi', 'Yok'),
('Personel', 'KPI Kontrol', 'Yok'),
('Personel', 'Personel Hijyen', 'Görüntüle'),
('Personel', 'Temizlik Kontrol', 'Yok'),
('Personel', 'Raporlama', 'Yok'),
('Personel', 'Ayarlar', 'Yok')
ON CONFLICT (rol_adi, modul_adi) DO NOTHING;

-- Depo Sorumlusu
INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES
('Depo Sorumlusu', 'Üretim Girişi', 'Düzenle'),
('Depo Sorumlusu', 'KPI Kontrol', 'Yok'),
('Depo Sorumlusu', 'Personel Hijyen', 'Yok'),
('Depo Sorumlusu', 'Temizlik Kontrol', 'Yok'),
('Depo Sorumlusu', 'Raporlama', 'Görüntüle'),
('Depo Sorumlusu', 'Ayarlar', 'Yok')
ON CONFLICT (rol_adi, modul_adi) DO NOTHING;

-- Doğrulama Sorguları
-- SELECT * FROM ayarlar_roller;
-- SELECT * FROM ayarlar_bolumler;
-- SELECT * FROM ayarlar_yetkiler ORDER BY rol_adi, modul_adi;
