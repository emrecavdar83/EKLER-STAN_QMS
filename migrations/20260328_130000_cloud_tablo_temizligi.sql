-- UP MIGRATION: Cloud Tablo Temizliği (Phase 2)
-- Çöp tabloların ve eski yedeklerin PostgreSQL (Supabase) tarafında temizlenmesi.

DROP TABLE IF EXISTS personel_backup_20260120 CASCADE;
DROP TABLE IF EXISTS ayarlar_kimyasallar CASCADE; -- (Yalnızca kimyasal_envanter kullanılacak)
DROP TABLE IF EXISTS gmp_lokasyonlar CASCADE;
DROP TABLE IF EXISTS gmp_denetim_kayitlari CASCADE;
DROP TABLE IF EXISTS qdms_okuma_onay CASCADE;

-- Eğer performans gereği "ayarlar_" tabloları daha da konsolide edilecekse buraya JSONB migrasyonu eklenebilir.
-- Şimdilik minimum müdahale ile en görünür atıklar silindi.

-- RLS (Row Level Security) Etkinleştirmeleri (PostgreSQL Spesifik)
-- Tüm ana tablolara RLS zorunlu (Ancak Supabase Dashboard'dan Policy yazılana kadar Bypass için disable bırakıldı)
-- ALTER TABLE personel ENABLE ROW LEVEL SECURITY;
