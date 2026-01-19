-- ==========================================
-- PERSONEL-ORGANİZASYON VERİ AKIŞI YENİDEN YAPILANDIRMA
-- ==========================================
-- Bu script personel tablosunu genişletir ve organizasyon şemasını
-- personel verilerinden otomatik oluşturur (Tek Kaynak Prensibi)

-- 1. PERSONEL TABLOSUNA YENİ SÜTUNLAR EKLE
-- departman_id: Personelin çalıştığı departman (Foreign Key)
-- yonetici_id: Personelin doğrudan yöneticisi (Self-referencing FK)
-- pozisyon_seviye: Hiyerarşik seviye (0: Yönetim Kurulu, 1: Genel Müdür, vb.)

ALTER TABLE personel 
ADD COLUMN IF NOT EXISTS departman_id INTEGER REFERENCES ayarlar_bolumler(id),
ADD COLUMN IF NOT EXISTS yonetici_id INTEGER REFERENCES personel(id),
ADD COLUMN IF NOT EXISTS pozisyon_seviye INTEGER DEFAULT 5;

-- 2. MEVCUT VERİLERİ OTOMATİK DÖNÜŞTÜR
-- Mevcut 'bolum' string değerlerini 'departman_id' foreign key'e dönüştür

-- 2a. Önce case-insensitive eşleştirme yap
UPDATE personel p
SET departman_id = (
    SELECT b.id 
    FROM ayarlar_bolumler b 
    WHERE UPPER(TRIM(b.bolum_adi)) = UPPER(TRIM(p.bolum))
    LIMIT 1
)
WHERE p.bolum IS NOT NULL 
  AND p.bolum != ''
  AND p.departman_id IS NULL;

-- 2b. Hiyerarşik eşleştirme (Örn: "Üretim > Krema" stringi için son parçayı al)
UPDATE personel p
SET departman_id = (
    SELECT b.id 
    FROM ayarlar_bolumler b 
    WHERE UPPER(TRIM(b.bolum_adi)) = UPPER(TRIM(
        CASE 
            WHEN p.bolum LIKE '%>%' THEN 
                TRIM(SUBSTRING(p.bolum FROM POSITION('>' IN REVERSE(p.bolum)) + 1))
            ELSE p.bolum
        END
    ))
    LIMIT 1
)
WHERE p.bolum IS NOT NULL 
  AND p.bolum != ''
  AND p.departman_id IS NULL;

-- 2c. Pozisyon seviyesini rol bazlı otomatik ata
UPDATE personel
SET pozisyon_seviye = CASE
    WHEN UPPER(rol) LIKE '%YÖNETİM KURULU%' OR UPPER(rol) LIKE '%BOARD%' THEN 0
    WHEN UPPER(rol) LIKE '%GENEL MÜDÜR%' OR UPPER(rol) LIKE '%CEO%' THEN 1
    WHEN UPPER(rol) LIKE '%DİREKTÖR%' OR UPPER(rol) LIKE '%DIRECTOR%' THEN 2
    WHEN UPPER(rol) LIKE '%MÜDÜR%' OR UPPER(rol) LIKE '%MANAGER%' THEN 3
    WHEN UPPER(rol) LIKE '%SORUMLU%' OR UPPER(rol) LIKE '%ŞEF%' OR UPPER(rol) LIKE '%SUPERVISOR%' THEN 4
    WHEN UPPER(rol) LIKE '%KOORDİNATÖR%' OR UPPER(rol) LIKE '%COORDINATOR%' THEN 4
    ELSE 5 -- Varsayılan: Personel seviyesi
END
WHERE pozisyon_seviye = 5; -- Sadece henüz atanmamışları güncelle

-- 3. ORGANİZASYON ŞEMASI VIEW'I OLUŞTUR
-- Bu view personel tablosundan otomatik olarak organizasyon şemasını oluşturur

CREATE OR REPLACE VIEW v_organizasyon_semasi AS
SELECT 
    p.id,
    p.ad_soyad,
    p.gorev,
    p.rol,
    p.pozisyon_seviye,
    p.yonetici_id,
    y.ad_soyad as yonetici_adi,
    d.bolum_adi as departman,
    d.id as departman_id,
    p.kullanici_adi,
    p.durum,
    p.vardiya,
    -- Hiyerarşik yol (Breadcrumb): "Genel Müdür > Üretim Müdürü > Vardiya Şefi"
    CASE 
        WHEN p.yonetici_id IS NULL THEN p.ad_soyad
        ELSE y.ad_soyad || ' > ' || p.ad_soyad
    END as hiyerarsi_yolu
FROM personel p
LEFT JOIN personel y ON p.yonetici_id = y.id
LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
WHERE p.ad_soyad IS NOT NULL
ORDER BY p.pozisyon_seviye, d.sira_no, p.ad_soyad;

-- 4. YARDIMCI VIEW: DEPARTMAN BAZLI PERSONEL SAYISI
CREATE OR REPLACE VIEW v_departman_personel_sayisi AS
SELECT 
    d.id as departman_id,
    d.bolum_adi,
    d.ana_departman_id,
    COUNT(p.id) as personel_sayisi,
    COUNT(CASE WHEN p.durum = 'AKTİF' THEN 1 END) as aktif_personel_sayisi
FROM ayarlar_bolumler d
LEFT JOIN personel p ON p.departman_id = d.id
WHERE d.aktif IS TRUE
GROUP BY d.id, d.bolum_adi, d.ana_departman_id
ORDER BY d.sira_no;

-- 5. İNDEKSLER (PERFORMANS İÇİN)
CREATE INDEX IF NOT EXISTS idx_personel_departman ON personel(departman_id);
CREATE INDEX IF NOT EXISTS idx_personel_yonetici ON personel(yonetici_id);
CREATE INDEX IF NOT EXISTS idx_personel_seviye ON personel(pozisyon_seviye);

-- 6. VERİ TUTARLILIĞI KONTROLÜ
-- Eşleşmeyen kayıtları raporla (Manuel düzeltme gerekebilir)
DO $$
DECLARE
    eslesmeyen_sayisi INTEGER;
BEGIN
    SELECT COUNT(*) INTO eslesmeyen_sayisi
    FROM personel
    WHERE bolum IS NOT NULL 
      AND bolum != ''
      AND departman_id IS NULL;
    
    IF eslesmeyen_sayisi > 0 THEN
        RAISE NOTICE 'UYARI: % adet personel kaydının departmanı eşleştirilemedi. Manuel kontrol gerekebilir.', eslesmeyen_sayisi;
        RAISE NOTICE 'Eşleşmeyen kayıtları görmek için: SELECT id, ad_soyad, bolum FROM personel WHERE bolum IS NOT NULL AND departman_id IS NULL;';
    ELSE
        RAISE NOTICE 'BAŞARILI: Tüm personel kayıtları departmanlara eşleştirildi.';
    END IF;
END $$;

-- BAŞARI MESAJI
SELECT 'Personel-Organizasyon veri akışı başarıyla yeniden yapılandırıldı!' as sonuc;
