-- ==========================================
-- SUPABASE (PostgreSQL) ORGANİZASYON ŞEMASI DÜZELTMESİ
-- ==========================================

-- 1. YENİ KOLONLARI EKLE (IF NOT EXISTS)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='personel' AND column_name='departman_id') THEN
        ALTER TABLE personel ADD COLUMN departman_id INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='personel' AND column_name='yonetici_id') THEN
        ALTER TABLE personel ADD COLUMN yonetici_id INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='personel' AND column_name='pozisyon_seviye') THEN
        ALTER TABLE personel ADD COLUMN pozisyon_seviye INTEGER DEFAULT 5;
    END IF;
END $$;

-- 2. POZİSYON SEVİYELERİNİ GÜNCELLE
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

-- 3. DEPARTMAN VIEW GÜNCELLEMESİ
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
WHERE p.ad_soyad IS NOT NULL AND (p.durum = 'AKTİF' OR p.durum IS NULL)
ORDER BY p.pozisyon_seviye, p.ad_soyad;
