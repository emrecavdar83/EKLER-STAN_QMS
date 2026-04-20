-- ANAYASA MADDE 31: Detaylı Personel Değişim Loglama
-- Her personel değişikliği zaman damgası ile kaydedilir
-- Field-level audit trail için

CREATE TABLE IF NOT EXISTS personel_degisim_loglari (
    id SERIAL PRIMARY KEY,
    personel_id INTEGER NOT NULL REFERENCES personel(id),
    alan_adi VARCHAR(100) NOT NULL,
    eski_deger TEXT,
    yeni_deger TEXT,
    degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
    degisim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    islem_tipi VARCHAR(50) DEFAULT 'UPDATE'
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_personel_degisim_personel_id ON personel_degisim_loglari(personel_id);
CREATE INDEX IF NOT EXISTS idx_personel_degisim_tarihi ON personel_degisim_loglari(degisim_tarihi);
CREATE INDEX IF NOT EXISTS idx_personel_degisim_alan ON personel_degisim_loglari(alan_adi);
