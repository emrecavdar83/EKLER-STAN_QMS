-- UP MIGRATION: Performans Optimizasyonu (İndeksleme)
-- Veri okuma hızını (Read Performance) artırmak için B-Tree İndeksleri

-- 1. Temizlik Modülü (Join & Filter)
-- Şema Doğrulaması: Plan tablosunda kat_id, bolum_id, ekipman_id mevcuttur.
CREATE INDEX IF NOT EXISTS idx_temizlik_plani_anahtar ON ayarlar_temizlik_plani(kat_id, bolum_id, ekipman_id);
CREATE INDEX IF NOT EXISTS idx_temizlik_plani_metot ON ayarlar_temizlik_plani(metot_id);

-- Kayıtlar tablosunda plan_id yoktur; lokasyon_id ve ekipman_id üzerinden sorgulanır.
CREATE INDEX IF NOT EXISTS idx_temizlik_kayitlari_lok_ekip_tarih ON temizlik_kayitlari(lokasyon_id, ekipman_id, tarih);

-- 2. Hiyerarşi ve Lokasyonlar (Recursive & Parent-Child)
CREATE INDEX IF NOT EXISTS idx_lokasyonlar_parent_id ON lokasyonlar(parent_id);
CREATE INDEX IF NOT EXISTS idx_lokasyonlar_tip ON lokasyonlar(tip);

-- 3. Yetkiler ve Güvenlik (Auth Performance)
CREATE INDEX IF NOT EXISTS idx_ayarlar_yetkiler_rol ON ayarlar_yetkiler(rol_adi);
CREATE INDEX IF NOT EXISTS idx_ayarlar_personel_auth ON personel(kullanici_adi, sifre);

-- 4. Üretim ve MAP Modülü
CREATE INDEX IF NOT EXISTS idx_vardiya_tarih_makina ON map_vardiya(tarih, makina_no);

-- DOWN MIGRATION
-- DROP INDEX IF EXISTS idx_temizlik_plani_anahtar;
-- DROP INDEX IF EXISTS idx_temizlik_plani_metot;
-- DROP INDEX IF EXISTS idx_temizlik_kayitlari_lok_ekip_tarih;
-- DROP INDEX IF EXISTS idx_lokasyonlar_parent_id;
-- DROP INDEX IF EXISTS idx_lokasyonlar_tip;
-- DROP INDEX IF EXISTS idx_ayarlar_yetkiler_rol;
-- DROP INDEX IF EXISTS idx_ayarlar_personel_auth;
-- DROP INDEX IF EXISTS idx_vardiya_tarih_makina;
