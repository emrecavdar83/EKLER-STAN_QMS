-- UP MIGRATION
-- gunluk_gorev_katalogu
CREATE TABLE IF NOT EXISTS gunluk_gorev_katalogu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kod VARCHAR(50) UNIQUE NOT NULL,
    ad VARCHAR(200) NOT NULL,
    kategori VARCHAR(100) NOT NULL,
    periyot VARCHAR(50) NOT NULL, -- gunluk, haftalik, aylik, yillik, manuel
    aciklama TEXT,
    olusturan_id INTEGER,
    aktif_mi BOOLEAN DEFAULT 1,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (olusturan_id) REFERENCES personel(id)
);

-- birlesik_gorev_havuzu
CREATE TABLE IF NOT EXISTS birlesik_gorev_havuzu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personel_id INTEGER NOT NULL,
    bolum_id INTEGER, -- Opsiyonel (Gorev yoneticiye tum bolum icin atandiginda bilgi amaciyla)
    gorev_kaynagi VARCHAR(50) NOT NULL, -- PERIYODIK, AKILLI_AKIS, QDMS, DOF, YONETIM vs.
    kaynak_id INTEGER NOT NULL, -- Katalog ID veya Flow Node ID
    atanma_tarihi DATE NOT NULL,
    hedef_tarih DATE NOT NULL,
    durum VARCHAR(50) DEFAULT 'BEKLIYOR', -- BEKLIYOR, TAMAMLANDI, SAPTI, IPTAL
    tamamlanma_tarihi DATETIME,
    sapma_notu TEXT,
    onaylayan_id INTEGER,
    FOREIGN KEY (personel_id) REFERENCES personel(id),
    FOREIGN KEY (bolum_id) REFERENCES ayarlar_bolumler(id),
    FOREIGN KEY (onaylayan_id) REFERENCES personel(id),
    UNIQUE(personel_id, gorev_kaynagi, kaynak_id, hedef_tarih)
);

CREATE INDEX IF NOT EXISTS idx_birlesik_gorev_personel ON birlesik_gorev_havuzu(personel_id);
CREATE INDEX IF NOT EXISTS idx_birlesik_gorev_kaynak ON birlesik_gorev_havuzu(gorev_kaynagi, kaynak_id);
CREATE INDEX IF NOT EXISTS idx_birlesik_gorev_tarih ON birlesik_gorev_havuzu(hedef_tarih);
CREATE INDEX IF NOT EXISTS idx_birlesik_gorev_bolum ON birlesik_gorev_havuzu(bolum_id);

-- DOWN MIGRATION (Ayrılabilir scriptte rollback için) 
-- DROP TABLE IF EXISTS birlesik_gorev_havuzu;
-- DROP TABLE IF EXISTS gunluk_gorev_katalogu;
