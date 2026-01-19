-- =============================================
-- DEPARTMAN (ESKİ BÖLÜMLER) TABLOSUNU SIFIRLAMA
-- =============================================
-- DİKKAT: Bu script SADECE 'ayarlar_bolumler' tablosunu temizler.
-- Lokasyonlar (Kat > Bölüm > Hat) SİLİNMEZ.

-- 1. Tabloyu Temizle
TRUNCATE TABLE ayarlar_bolumler RESTART IDENTITY;

-- 2. Varsayılan Departmanları Tekrar Ekle (İsteğe Bağlı)
-- Eğer tamamen boş kalmasını istemiyorsanız aşağıdaki satırı açıp çalıştırabilirsiniz.
-- INSERT INTO ayarlar_bolumler (bolum_adi, sira_no, aciklama) VALUES 
-- ('Üretim', 10, 'Üretim Sahası'),
-- ('Kalite', 20, 'Kalite Güvence ve Kontrol'),
-- ('Bakım', 30, 'Teknik Bakım'),
-- ('Depo', 40, 'Hammadde ve Ürün Depo'),
-- ('Yönetim', 50, 'Fabrika Yönetimi');
