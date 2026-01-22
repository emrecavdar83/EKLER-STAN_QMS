# Personel Organizasyon Şeması Düzeltme Talimatları

## Sorun
Personel organizasyon şemasında müdürler "Şef/Koordinatör" kategorisinde görünüyor. Bunun sebebi `pozisyon_seviye` kolonunun eksik olması.

## Çözüm Adımları

### 1. Supabase SQL Editor'de Migration Çalıştırma

1. **Supabase Dashboard**'a gidin: https://supabase.com/dashboard
2. Projenizi seçin
3. Sol menüden **SQL Editor**'ü açın
4. **New Query** butonuna tıklayın
5. Aşağıdaki SQL scriptini yapıştırın ve **RUN** butonuna basın:

```sql
-- PERSONEL ORGANİZASYON ŞEMASI DÜZELTMESİ
-- Müdürlerin doğru kategoride görünmesi için pozisyon_seviye kolonu eklenir

-- 1. YENİ KOLONLARI EKLE
ALTER TABLE personel 
ADD COLUMN IF NOT EXISTS departman_id INTEGER,
ADD COLUMN IF NOT EXISTS yonetici_id INTEGER,
ADD COLUMN IF NOT EXISTS pozisyon_seviye INTEGER DEFAULT 5;

-- 2. POZİSYON SEVİYELERİNİ ROL BAZLI OTOMATİK ATA
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

-- 3. DEPARTMAN ID'LERİNİ EŞLEŞTİR
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

-- 4. FOREIGN KEY CONSTRAINT'LERİ EKLE
ALTER TABLE personel DROP CONSTRAINT IF EXISTS personel_departman_id_fkey;
ALTER TABLE personel DROP CONSTRAINT IF EXISTS personel_yonetici_id_fkey;

ALTER TABLE personel 
ADD CONSTRAINT personel_departman_id_fkey 
    FOREIGN KEY (departman_id) REFERENCES ayarlar_bolumler(id) ON DELETE SET NULL;

ALTER TABLE personel 
ADD CONSTRAINT personel_yonetici_id_fkey 
    FOREIGN KEY (yonetici_id) REFERENCES personel(id) ON DELETE SET NULL;

-- 5. VIEW OLUŞTUR
CREATE OR REPLACE VIEW v_organizasyon_semasi AS
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

-- 6. İNDEKSLER (PERFORMANS İÇİN)
CREATE INDEX IF NOT EXISTS idx_personel_departman ON personel(departman_id);
CREATE INDEX IF NOT EXISTS idx_personel_yonetici ON personel(yonetici_id);
CREATE INDEX IF NOT EXISTS idx_personel_seviye ON personel(pozisyon_seviye);

-- 7. KONTROL SORGUSU
SELECT 
    pozisyon_seviye,
    CASE pozisyon_seviye
        WHEN 0 THEN '🏛️ Yönetim Kurulu'
        WHEN 1 THEN '👑 Genel Müdür'
        WHEN 2 THEN '📊 Müdürler'
        WHEN 3 THEN '🎯 Şef/Koordinatör'
        ELSE '👥 Personel'
    END as kategori,
    COUNT(*) as kisi_sayisi
FROM personel
WHERE ad_soyad IS NOT NULL
GROUP BY pozisyon_seviye
ORDER BY pozisyon_seviye;
```

### 2. Streamlit Cloud'da Uygulamayı Yeniden Başlatma

1. **Streamlit Cloud Dashboard**'a gidin: https://share.streamlit.io/
2. Uygulamanızı bulun
3. **⋮** (üç nokta) menüsüne tıklayın
4. **Reboot app** seçeneğini seçin
5. Uygulama yeniden başladıktan sonra giriş yapın
6. **Kurumsal Raporlama > Personel Organizasyon Şeması** bölümüne gidin
7. Müdürlerin artık **"📊 Müdürler"** kategorisinde göründüğünü doğrulayın

## Beklenen Sonuç

✅ **Müdürler** (EMRE ÇAVDAR, MUSTAFA AVŞAR) → "📊 Müdürler" kategorisinde
✅ **Şef/Koordinatörler** → "🎯 Şef/Koordinatör" kategorisinde
✅ **Diğer personel** → "👥 Personel Listeleri" bölümünde

## Pozisyon Seviyeleri

- **Seviye 0**: Yönetim Kurulu
- **Seviye 1**: Genel Müdür
- **Seviye 2**: Müdürler (Direktörler)
- **Seviye 3**: Şef/Koordinatör/Sorumlu
- **Seviye 4**: Kıdemli Personel
- **Seviye 5**: Personel (Varsayılan)
