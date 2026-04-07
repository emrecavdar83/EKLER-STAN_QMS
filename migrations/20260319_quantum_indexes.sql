-- MAP performans indeksleri
CREATE INDEX IF NOT EXISTS idx_map_zaman_vid ON map_zaman_cizelgesi (vardiya_id);
CREATE INDEX IF NOT EXISTS idx_map_fire_vid ON map_fire_kaydi (vardiya_id);

-- QDMS tabloları için ek indeksler
CREATE INDEX IF NOT EXISTS idx_qdms_belgeler_durum ON qdms_belgeler (durum);
CREATE INDEX IF NOT EXISTS idx_qdms_belgeler_kod ON qdms_belgeler (belge_kodu);
CREATE INDEX IF NOT EXISTS idx_qdms_okuma_personel ON qdms_okuma_onay (personel_id, belge_kodu);
