-- ============================================================
-- EKLERİSTAN QMS | Migration: v8.6 | 2026-04-20
-- EKSIK TABLO VE VIEW OLUŞTURMA
-- ============================================================
-- Sorun: Supabase'de 'personel' tablosu ve 'tum_personel' VIEW'ı
--        tanımlanmamış olduğu için program çalışmıyor.
-- Hedef: Bu script'i Supabase SQL Editor'a yapıştırarak çalıştır.
-- ============================================================

BEGIN;

-- ============================================================
-- 1. 'personel' TABLOSUNU OLUŞTUR
-- ============================================================
-- Bu tablo, tüm fabrika çalışanlarının ana kaydını tutar.
-- 'ayarlar_kullanicilar' ise sadece sisteme login edebilenleri içerir.
-- Her iki tablonun ID'leri birebir eşleştirilir.
-- ============================================================

CREATE TABLE IF NOT EXISTS personel (
    id                    SERIAL PRIMARY KEY,
    ad_soyad              TEXT,
    kullanici_adi         VARCHAR(100) UNIQUE,
    sifre                 TEXT,
    rol                   VARCHAR(100),
    gorev                 TEXT,
    vardiya               VARCHAR(100),
    durum                 VARCHAR(50)  DEFAULT 'AKTİF',
    ise_giris_tarihi      DATE,
    izin_gunu             VARCHAR(100),
    departman_id          INTEGER,
    yonetici_id           INTEGER,
    pozisyon_seviye       VARCHAR(50),
    is_cikis_tarihi       DATE,
    ayrilma_sebebi        TEXT,
    bolum                 VARCHAR(255),
    sorumlu_bolum         VARCHAR(255),
    kat                   VARCHAR(50),
    telefon_no            VARCHAR(50),
    servis_duragi         TEXT,
    guncelleme_tarihi     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    operasyonel_bolum_id  INTEGER,
    ikincil_yonetici_id   INTEGER,
    baslama_tarihi        DATE,
    vekil_id              INTEGER,
    aktif_izinde_mi       INTEGER      DEFAULT 0,
    ayrilma_tarihi        DATE,
    ayrilma_nedeni        TEXT,
    qms_departman_id      INTEGER
);

-- ============================================================
-- 2. MEVCUT 'ayarlar_kullanicilar' KAYITLARINI PERSONELE KOPYALA
-- ============================================================
-- Eğer ayarlar_kullanicilar'da kayıt varsa, personel tablosuna
-- aktarılır. ID'ler korunur (ON CONFLICT DO NOTHING).
-- ============================================================

INSERT INTO personel (
    id, ad_soyad, kullanici_adi, sifre, rol, gorev, vardiya, durum,
    ise_giris_tarihi, izin_gunu, departman_id, yonetici_id,
    pozisyon_seviye, is_cikis_tarihi, ayrilma_sebebi, bolum,
    sorumlu_bolum, kat, telefon_no, servis_duragi, guncelleme_tarihi,
    operasyonel_bolum_id, ikincil_yonetici_id, baslama_tarihi, vekil_id,
    aktif_izinde_mi, ayrilma_tarihi, ayrilma_nedeni, qms_departman_id
)
SELECT
    id, ad_soyad, kullanici_adi, sifre, rol, gorev, vardiya, durum,
    ise_giris_tarihi, izin_gunu, departman_id, yonetici_id,
    pozisyon_seviye, is_cikis_tarihi, ayrilma_sebebi, bolum,
    sorumlu_bolum, kat, telefon_no, servis_duragi, guncelleme_tarihi,
    operasyonel_bolum_id, ikincil_yonetici_id, baslama_tarihi, vekil_id,
    aktif_izinde_mi, ayrilma_tarihi, ayrilma_nedeni, qms_departman_id
FROM ayarlar_kullanicilar
ON CONFLICT (id) DO NOTHING;

-- SEQUENCE senkronizasyonu (INSERT sonrası otomatik ID çakışmaları önlenir)
SELECT setval('personel_id_seq', COALESCE((SELECT MAX(id) FROM personel), 1));

-- ============================================================
-- 3. 'tum_personel' VIEW'INI OLUŞTUR
-- ============================================================
-- Bu VIEW, personel ve ayarlar_kullanicilar tablolarını birleştirir.
-- Kodun birçok yerinde "FROM tum_personel p" olarak kullanılmaktadır.
-- ============================================================

DROP VIEW IF EXISTS tum_personel;

CREATE VIEW tum_personel AS
    -- Personel tablosundan tüm kayıtlar
    SELECT
        p.id,
        p.ad_soyad,
        p.kullanici_adi,
        p.sifre,
        p.rol,
        p.gorev,
        p.vardiya,
        p.durum,
        p.ise_giris_tarihi,
        p.izin_gunu,
        p.departman_id,
        p.yonetici_id,
        p.pozisyon_seviye,
        p.is_cikis_tarihi,
        p.ayrilma_sebebi,
        p.bolum,
        p.sorumlu_bolum,
        p.kat,
        p.telefon_no,
        p.servis_duragi,
        p.guncelleme_tarihi,
        p.operasyonel_bolum_id,
        p.ikincil_yonetici_id,
        p.baslama_tarihi,
        p.vekil_id,
        p.aktif_izinde_mi,
        p.ayrilma_tarihi,
        p.ayrilma_nedeni,
        p.qms_departman_id
    FROM personel p

    UNION

    -- ayarlar_kullanicilar'dan, personel'de OLMAYAN kullanıcılar (login hesabı ama personel kaydı yok)
    SELECT
        u.id,
        u.ad_soyad,
        u.kullanici_adi,
        u.sifre,
        u.rol,
        u.gorev,
        u.vardiya,
        u.durum,
        u.ise_giris_tarihi,
        u.izin_gunu,
        u.departman_id,
        u.yonetici_id,
        u.pozisyon_seviye,
        u.is_cikis_tarihi,
        u.ayrilma_sebebi,
        u.bolum,
        u.sorumlu_bolum,
        u.kat,
        u.telefon_no,
        u.servis_duragi,
        u.guncelleme_tarihi,
        u.operasyonel_bolum_id,
        u.ikincil_yonetici_id,
        u.baslama_tarihi,
        u.vekil_id,
        u.aktif_izinde_mi,
        u.ayrilma_tarihi,
        u.ayrilma_nedeni,
        u.qms_departman_id
    FROM ayarlar_kullanicilar u
    WHERE u.id NOT IN (SELECT id FROM personel);

-- ============================================================
-- 4. RLS (ROW LEVEL SECURITY) AKTİF ET
-- ============================================================
ALTER TABLE personel ENABLE ROW LEVEL SECURITY;

-- Uygulama servis rolüne tam erişim ver
-- NOT: Supabase'de "service_role" zaten RLS'yi bypass eder.
-- Eğer anon veya authenticated erişimi gerekiyorsa aşağıyı ekle:
-- CREATE POLICY "allow_authenticated" ON personel
--     FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- ============================================================
-- 5. DOĞRULAMA
-- ============================================================
SELECT 'personel' as tablo, COUNT(*) as kayit_sayisi FROM personel
UNION ALL
SELECT 'ayarlar_kullanicilar', COUNT(*) FROM ayarlar_kullanicilar
UNION ALL
SELECT 'tum_personel (view)', COUNT(*) FROM tum_personel;

COMMIT;
