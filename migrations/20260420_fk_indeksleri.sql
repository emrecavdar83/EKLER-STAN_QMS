-- migrations/20260420_fk_indeksleri.sql
-- Anayasa Madde 14 uyumu: FK ve filtre kolonları indeksleme

-- map_vardiya tablosu
CREATE INDEX IF NOT EXISTS idx_map_vardiya_urun_adi
    ON map_vardiya(urun_adi);

CREATE INDEX IF NOT EXISTS idx_map_vardiya_tarih
    ON map_vardiya(tarih);

CREATE INDEX IF NOT EXISTS idx_map_vardiya_acan_kullanici
    ON map_vardiya(acan_kullanici_id);

-- gunluk_gorevler tablosu silindi (Mevcut tablolar: gunluk_gorev_katalogu, birlesik_gorev_havuzu)

-- birlesik_gorev_havuzu tablosu
CREATE INDEX IF NOT EXISTS idx_bgv_personel_id
    ON birlesik_gorev_havuzu(personel_id);

CREATE INDEX IF NOT EXISTS idx_bgv_atanma_tarihi
    ON birlesik_gorev_havuzu(atanma_tarihi);

CREATE INDEX IF NOT EXISTS idx_bgv_atayan_id
    ON birlesik_gorev_havuzu(atayan_id);
