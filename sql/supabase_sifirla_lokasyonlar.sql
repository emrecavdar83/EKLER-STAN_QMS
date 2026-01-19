-- ⚠️ DİKKAT: BU KOMUTLAR TÜM LOKASYON VERİLERİNİ SİLER!
-- "Mevcut lokasyonları silip sıfırdan yapmak" için kullanılır.

-- 1. Lokasyon Proses Atamalarını ve Lokasyonları temizle
-- CASCADE sayesinde atamalar da otomatik silinir
-- RESTART IDENTITY sayesinde ID'ler tekrar 1'den başlar
TRUNCATE TABLE lokasyonlar RESTART IDENTITY CASCADE;

-- ALTERNATİF: Sadece verileri silmek (ID'ler kaldığı yerden devam eder)
-- DELETE FROM lokasyonlar;

-- 2. (İsteğe Bağlı) Temizlik sonrası varsayılan Katları otomatik ekle
-- Eğer tamamen boş kalsın istiyorsanız bu kısmı çalıştırmayın.
/*
INSERT INTO lokasyonlar (ad, tip, parent_id, sira_no) VALUES
('KAT 1 - ÜRETİM', 'Kat', NULL, 1),
('KAT 2 - PAKETLEME', 'Kat', NULL, 2),
('DEPO ALANI', 'Kat', NULL, 3);
*/
