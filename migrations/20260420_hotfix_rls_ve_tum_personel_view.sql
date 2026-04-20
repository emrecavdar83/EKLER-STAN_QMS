-- ============================================================
-- EKLERİSTAN QMS | Hotfix: v8.6.2 | 2026-04-20
-- tum_personel VIEW (tip uyumu ile) + RLS POLİTİKALARI
-- ============================================================

DROP VIEW IF EXISTS tum_personel;

CREATE VIEW tum_personel AS
    SELECT
        p.id,
        p.ad_soyad,
        p.kullanici_adi,
        p.sifre,
        p.rol,
        p.gorev,
        p.vardiya,
        p.durum,
        p.ise_giris_tarihi::TEXT      AS ise_giris_tarihi,
        p.izin_gunu,
        p.departman_id,
        p.yonetici_id,
        p.pozisyon_seviye::TEXT       AS pozisyon_seviye,
        p.is_cikis_tarihi::TEXT       AS is_cikis_tarihi,
        p.ayrilma_sebebi,
        p.bolum,
        p.sorumlu_bolum,
        p.kat,
        p.telefon_no,
        p.servis_duragi,
        p.guncelleme_tarihi,
        p.operasyonel_bolum_id,
        p.ikincil_yonetici_id,
        p.baslama_tarihi::TEXT        AS baslama_tarihi,
        p.vekil_id,
        p.aktif_izinde_mi,
        p.ayrilma_tarihi::TEXT        AS ayrilma_tarihi,
        p.ayrilma_nedeni,
        p.qms_departman_id
    FROM personel p

    UNION

    SELECT
        u.id,
        u.ad_soyad,
        u.kullanici_adi,
        u.sifre,
        u.rol,
        u.gorev,
        u.vardiya,
        u.durum,
        u.ise_giris_tarihi::TEXT      AS ise_giris_tarihi,
        u.izin_gunu,
        u.departman_id,
        u.yonetici_id,
        u.pozisyon_seviye::TEXT       AS pozisyon_seviye,
        u.is_cikis_tarihi::TEXT       AS is_cikis_tarihi,
        u.ayrilma_sebebi,
        u.bolum,
        u.sorumlu_bolum,
        u.kat,
        u.telefon_no,
        u.servis_duragi,
        u.guncelleme_tarihi,
        u.operasyonel_bolum_id,
        u.ikincil_yonetici_id,
        u.baslama_tarihi::TEXT        AS baslama_tarihi,
        u.vekil_id,
        u.aktif_izinde_mi,
        u.ayrilma_tarihi::TEXT        AS ayrilma_tarihi,
        u.ayrilma_nedeni,
        u.qms_departman_id
    FROM ayarlar_kullanicilar u
    WHERE u.id NOT IN (SELECT id FROM personel);


-- RLS POLİTİKALARI
DROP POLICY IF EXISTS "personel_select_policy" ON personel;
DROP POLICY IF EXISTS "personel_insert_policy" ON personel;
DROP POLICY IF EXISTS "personel_update_policy" ON personel;
DROP POLICY IF EXISTS "personel_delete_policy" ON personel;

CREATE POLICY "personel_select_policy" ON personel FOR SELECT USING (true);
CREATE POLICY "personel_insert_policy" ON personel FOR INSERT WITH CHECK (true);
CREATE POLICY "personel_update_policy" ON personel FOR UPDATE USING (true) WITH CHECK (true);
CREATE POLICY "personel_delete_policy" ON personel FOR DELETE USING (true);

-- DOĞRULAMA
SELECT 'personel' as nesne, COUNT(*) as kayit FROM personel
UNION ALL SELECT 'tum_personel', COUNT(*) FROM tum_personel;
