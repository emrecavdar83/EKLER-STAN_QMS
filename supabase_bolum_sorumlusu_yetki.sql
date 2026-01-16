-- Bölüm Sorumlusu Rolü İçin Yetki Matrisi
-- Supabase'de çalıştırılacak SQL

-- 1. Bölüm Sorumlusu rolünü ekle
INSERT INTO ayarlar_roller (rol_adi, aciklama, aktif) VALUES
('Bölüm Sorumlusu', 'Bölüm operasyonları yönetimi - Kendi bölümü ile sınırlı', TRUE)
ON CONFLICT (rol_adi) DO NOTHING;

-- 2. Bölüm Sorumlusu için yetki matrisi
-- Modüller: Üretim Girişi, KPI Kontrol, GMP Denetimi, Personel Hijyen, Temizlik Kontrol, Raporlama, Ayarlar

INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES
('Bölüm Sorumlusu', 'Üretim Girişi', 'Düzenle'),
('Bölüm Sorumlusu', 'KPI Kontrol', 'Düzenle'),
('Bölüm Sorumlusu', 'GMP Denetimi', 'Görüntüle'),
('Bölüm Sorumlusu', 'Personel Hijyen', 'Görüntüle'),
('Bölüm Sorumlusu', 'Temizlik Kontrol', 'Görüntüle'),
('Bölüm Sorumlusu', 'Raporlama', 'Görüntüle'),
('Bölüm Sorumlusu', 'Ayarlar', 'Yok')
ON CONFLICT (rol_adi, modul_adi) DO UPDATE SET erisim_turu = EXCLUDED.erisim_turu;

-- Doğrulama
SELECT * FROM ayarlar_yetkiler WHERE rol_adi = 'Bölüm Sorumlusu' ORDER BY modul_adi;
