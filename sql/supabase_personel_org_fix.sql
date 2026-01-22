-- PERSONEL ORGANİZASYON ŞEMASI DÜZELTMESİ
-- Müdürlerin pozisyon_seviye değerlerini güncelle (kolon zaten var)

-- 1. POZİSYON SEVİYELERİNİ ROL VE GÖREV BAZLI OTOMATİK ATA
UPDATE personel
SET pozisyon_seviye = CASE
    WHEN UPPER(COALESCE(rol, '')) LIKE '%YÖNETİM KURULU%' OR UPPER(COALESCE(rol, '')) LIKE '%BOARD%' THEN 0
    WHEN UPPER(COALESCE(rol, '')) LIKE '%GENEL MÜDÜR%' OR UPPER(COALESCE(rol, '')) LIKE '%CEO%' THEN 1
    WHEN UPPER(COALESCE(rol, '')) LIKE '%DİREKTÖR%' OR UPPER(COALESCE(rol, '')) LIKE '%DIRECTOR%' THEN 2
    WHEN UPPER(COALESCE(rol, '')) LIKE '%MÜDÜR%' OR UPPER(COALESCE(rol, '')) LIKE '%MANAGER%' THEN 2
    WHEN UPPER(COALESCE(gorev, '')) LIKE '%MÜDÜR%' OR UPPER(COALESCE(gorev, '')) LIKE '%MANAGER%' THEN 2
    WHEN UPPER(COALESCE(rol, '')) LIKE '%SORUMLU%' OR UPPER(COALESCE(rol, '')) LIKE '%ŞEF%' OR UPPER(COALESCE(rol, '')) LIKE '%SUPERVISOR%' THEN 3
    WHEN UPPER(COALESCE(rol, '')) LIKE '%KOORDİNATÖR%' OR UPPER(COALESCE(rol, '')) LIKE '%COORDINATOR%' THEN 3
    WHEN UPPER(COALESCE(gorev, '')) LIKE '%ŞEF%' OR UPPER(COALESCE(gorev, '')) LIKE '%SORUMLU%' THEN 3
    WHEN UPPER(COALESCE(gorev, '')) LIKE '%KOORDİNATÖR%' THEN 3
    ELSE 5
END
WHERE pozisyon_seviye IS NULL OR pozisyon_seviye = 5;

-- 2. KONTROL SORGUSU - Pozisyon dağılımını göster
SELECT 
    pozisyon_seviye,
    CASE pozisyon_seviye
        WHEN 0 THEN 'Yönetim Kurulu'
        WHEN 1 THEN 'Genel Müdür'
        WHEN 2 THEN 'Müdürler'
        WHEN 3 THEN 'Şef/Koordinatör'
        ELSE 'Personel'
    END as kategori,
    COUNT(*) as kisi_sayisi,
    STRING_AGG(ad_soyad, ', ' ORDER BY ad_soyad) as kisi_listesi
FROM personel
WHERE ad_soyad IS NOT NULL
GROUP BY pozisyon_seviye
ORDER BY pozisyon_seviye;
