-- EKLERİSTAN QMS - GRAND UNIFICATION (v7.0)
-- Migration: personel -> ayarlar_kullanicilar

BEGIN;

-- 1. Create the new table with standardized name (Ensuring all 29 columns from legacy 'personel')
DROP TABLE IF EXISTS ayarlar_kullanicilar CASCADE;
CREATE TABLE ayarlar_kullanicilar (
    id SERIAL PRIMARY KEY,
    ad_soyad TEXT,
    kullanici_adi VARCHAR(100) UNIQUE NOT NULL,
    sifre TEXT,
    rol VARCHAR(100),
    gorev TEXT,
    vardiya VARCHAR(100),
    durum VARCHAR(50) DEFAULT 'AKTİF',
    ise_giris_tarihi DATE,
    izin_gunu VARCHAR(100),
    departman_id INTEGER,
    yonetici_id INTEGER,
    pozisyon_seviye VARCHAR(100),
    is_cikis_tarihi DATE,
    ayrilma_sebebi TEXT,
    bolum VARCHAR(255),
    sorumlu_bolum VARCHAR(255),
    kat VARCHAR(50),
    telefon_no VARCHAR(50),
    servis_duragi TEXT,
    guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operasyonel_bolum_id INTEGER,
    ikincil_yonetici_id INTEGER,
    baslama_tarihi DATE,
    vekil_id INTEGER,
    aktif_izinde_mi INTEGER DEFAULT 0,
    ayrilma_tarihi DATE,
    ayrilma_nedeni TEXT,
    qms_departman_id INTEGER
);

-- 2. Migrate Data with explicit column mapping
INSERT INTO ayarlar_kullanicilar (
    ad_soyad, kullanici_adi, sifre, rol, gorev, vardiya, durum, ise_giris_tarihi, izin_gunu, 
    id, departman_id, yonetici_id, pozisyon_seviye, is_cikis_tarihi, ayrilma_sebebi, 
    bolum, sorumlu_bolum, kat, telefon_no, servis_duragi, guncelleme_tarihi, 
    operasyonel_bolum_id, ikincil_yonetici_id, baslama_tarihi, vekil_id, 
    aktif_izinde_mi, ayrilma_tarihi, ayrilma_nedeni, qms_departman_id
)
SELECT 
    ad_soyad, kullanici_adi, sifre, rol, gorev, vardiya, durum, ise_giris_tarihi, izin_gunu, 
    id, departman_id, yonetici_id, pozisyon_seviye, is_cikis_tarihi, ayrilma_sebebi, 
    bolum, sorumlu_bolum, kat, telefon_no, servis_duragi, guncelleme_tarihi, 
    operasyonel_bolum_id, ikincil_yonetici_id, baslama_tarihi, vekil_id, 
    aktif_izinde_mi, ayrilma_tarihi, ayrilma_nedeni, qms_departman_id
FROM personel
ON CONFLICT (kullanici_adi) DO NOTHING;

-- 3. Update Foreign Key Constraints in other tables
-- Note: We need to drop existing constraints pointing to 'personel' and point them to 'ayarlar_kullanicilar'

-- qms_departmanlar
ALTER TABLE qms_departmanlar DROP CONSTRAINT IF EXISTS qms_departmanlar_yonetici_id_fkey;
ALTER TABLE qms_departmanlar ADD CONSTRAINT qms_departmanlar_yonetici_id_fkey FOREIGN KEY (yonetici_id) REFERENCES ayarlar_kullanicilar(id);

-- qdms_belgeler
ALTER TABLE qdms_belgeler DROP CONSTRAINT IF EXISTS qdms_belgeler_olusturan_id_fkey;
ALTER TABLE qdms_belgeler ADD CONSTRAINT qdms_belgeler_olusturan_id_fkey FOREIGN KEY (olusturan_id) REFERENCES ayarlar_kullanicilar(id);

-- qdms_revizyon_log
ALTER TABLE qdms_revizyon_log DROP CONSTRAINT IF EXISTS qdms_revizyon_log_degistiren_id_fkey;
ALTER TABLE qdms_revizyon_log ADD CONSTRAINT qdms_revizyon_log_degistiren_id_fkey FOREIGN KEY (degistiren_id) REFERENCES ayarlar_kullanicilar(id);

-- qdms_yayim
ALTER TABLE qdms_yayim DROP CONSTRAINT IF EXISTS qdms_yayim_yayimlayan_id_fkey;
ALTER TABLE qdms_yayim ADD CONSTRAINT qdms_yayim_yayimlayan_id_fkey FOREIGN KEY (yayimlayan_id) REFERENCES ayarlar_kullanicilar(id);

-- qdms_okuma_onay
ALTER TABLE qdms_okuma_onay DROP CONSTRAINT IF EXISTS qdms_okuma_onay_personel_id_fkey;
ALTER TABLE qdms_okuma_onay ADD CONSTRAINT qdms_okuma_onay_personel_id_fkey FOREIGN KEY (personel_id) REFERENCES ayarlar_kullanicilar(id);

-- soguk_oda_planlama_kurallari
ALTER TABLE soguk_oda_planlama_kurallari DROP CONSTRAINT IF EXISTS soguk_oda_planlama_kurallari_oda_id_fkey;
-- (Oda id actually points to soguk_odalar, not personel. Skipping unrelated FKs)

-- 4. Enable RLS on new table
ALTER TABLE ayarlar_kullanicilar ENABLE ROW LEVEL SECURITY;

-- 5. Create a view for backward compatibility (Optional, for transition phase)
-- DROP TABLE personel; -- NOT DROPPING YET, for safety
-- CREATE VIEW personel AS SELECT * FROM ayarlar_kullanicilar;

COMMIT;
