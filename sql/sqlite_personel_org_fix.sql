-- ==========================================
-- PERSONEL ORGANİZASYON ŞEMASI DÜZELTMESİ (SQLite)
-- ==========================================
-- Müdürlerin doğru kategoride görünmesi için gerekli kolonları ekler

-- 1. YENİ KOLONLARI EKLE
ALTER TABLE personel ADD COLUMN departman_id INTEGER;
ALTER TABLE personel ADD COLUMN yonetici_id INTEGER;
ALTER TABLE personel ADD COLUMN pozisyon_seviye INTEGER DEFAULT 5;

-- 2. POZİSYON SEVİYELERİNİ ROL BAZLI OTOMATİK ATA
-- Seviye 0: Yönetim Kurulu
-- Seviye 1: Genel Müdür
-- Seviye 2: Direktörler
-- Seviye 3: Müdürler
-- Seviye 4: Şef/Koordinatör
-- Seviye 5: Personel (Varsayılan)

UPDATE personel
SET pozisyon_seviye = CASE
    WHEN UPPER(rol) LIKE '%YÖNETİM KURULU%' OR UPPER(rol) LIKE '%BOARD%' THEN 0
    WHEN UPPER(rol) LIKE '%GENEL MÜDÜR%' OR UPPER(rol) LIKE '%CEO%' THEN 1
    WHEN UPPER(rol) LIKE '%DİREKTÖR%' OR UPPER(rol) LIKE '%DIRECTOR%' THEN 2
    WHEN UPPER(rol) LIKE '%MÜDÜR%' OR UPPER(rol) LIKE '%MANAGER%' THEN 2
    WHEN UPPER(gorev) LIKE '%MÜDÜR%' OR UPPER(gorev) LIKE '%MANAGER%' THEN 2
    WHEN UPPER(rol) LIKE '%SORUMLU%' OR UPPER(rol) LIKE '%ŞEF%' OR UPPER(rol) LIKE '%SUPERVISOR%' THEN 3
    WHEN UPPER(rol) LIKE '%KOORDİNATÖR%' OR UPPER(rol) LIKE '%COORDINATOR%' THEN 3
    WHEN UPPER(gorev) LIKE '%ŞEF%' OR UPPER(gorev) LIKE '%SORUMLU%' THEN 3
    WHEN UPPER(gorev) LIKE '%KOORDİNATÖR%' THEN 3
    ELSE 5
END
WHERE pozisyon_seviye = 5 OR pozisyon_seviye IS NULL;

-- 3. DEPARTMAN ID'LERİNİ EŞLEŞTİR (bolum string -> departman_id)
-- Önce tam eşleşme dene
UPDATE personel
SET departman_id = (
    SELECT id 
    FROM ayarlar_bolumler 
    WHERE UPPER(TRIM(bolum_adi)) = UPPER(TRIM(personel.bolum))
    LIMIT 1
)
WHERE bolum IS NOT NULL 
  AND bolum != ''
  AND departman_id IS NULL;

-- 4. VIEW OLUŞTUR (SQLite için basitleştirilmiş)
DROP VIEW IF EXISTS v_organizasyon_semasi;

CREATE VIEW v_organizasyon_semasi AS
SELECT 
    p.id,
    p.ad_soyad,
    p.gorev,
    p.rol,
    p.pozisyon_seviye,
    p.yonetici_id,
    y.ad_soyad as yonetici_adi,
    COALESCE(d.bolum_adi, p.bolum, 'Tanımsız') as departman,
    d.id as departman_id,
    p.kullanici_adi,
    p.durum,
    p.vardiya
FROM personel p
LEFT JOIN personel y ON p.yonetici_id = y.id
LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
WHERE p.ad_soyad IS NOT NULL
ORDER BY p.pozisyon_seviye, p.ad_soyad;

-- 5. KONTROL SORGUSU
SELECT 
    pozisyon_seviye,
    CASE pozisyon_seviye
        WHEN 0 THEN '🏛️ Yönetim Kurulu'
        WHEN 1 THEN '👑 Genel Müdür'
        WHEN 2 THEN '📊 Müdürler'
        WHEN 3 THEN '🎯 Şef/Koordinatör'
        ELSE '👥 Personel'
    END as kategori,
    COUNT(*) as kisi_sayisi,
    GROUP_CONCAT(ad_soyad, ', ') as kisi_listesi
FROM personel
WHERE ad_soyad IS NOT NULL
GROUP BY pozisyon_seviye
ORDER BY pozisyon_seviye;
