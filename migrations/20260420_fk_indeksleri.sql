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

