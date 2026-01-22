-- ADIM 1: Mevcut Müdürleri Seviye 2'den 3'e Taşı
-- Bu işlem kurumsal standarda uyum sağlar (Direktör > Müdür hiyerarşisi)

-- Önce kontrol: Hangi kayıtlar etkilenecek?
SELECT 
    ad_soyad, 
    gorev, 
    pozisyon_seviye as eski_seviye,
    3 as yeni_seviye
FROM personel
WHERE pozisyon_seviye = 2;

-- Eğer sonuçlar doğruysa, aşağıdaki UPDATE'i çalıştırın:
UPDATE personel
SET pozisyon_seviye = 3
WHERE pozisyon_seviye = 2;

-- Kontrol: Yeni dağılım
SELECT 
    pozisyon_seviye,
    COUNT(*) as kisi_sayisi,
    STRING_AGG(ad_soyad, ', ' ORDER BY ad_soyad) as kisi_listesi
FROM personel
WHERE ad_soyad IS NOT NULL
GROUP BY pozisyon_seviye
ORDER BY pozisyon_seviye;
