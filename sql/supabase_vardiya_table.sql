-- Supabase (PostgreSQL) için Vardiya Programı Tablosu
-- Bu scripti Supabase SQL Editor üzerinden çalıştırın.

CREATE TABLE IF NOT EXISTS personel_vardiya_programi (
    id SERIAL PRIMARY KEY,
    personel_id INTEGER NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    vardiya TEXT NOT NULL,          -- Örn: 'GÜNDÜZ VARDİYASI', 'GECE VARDİYASI', 'ARA VARDİYA'
    izin_gunleri TEXT,              -- Örn: 'Pazar' veya 'Cumartesi,Pazar' (Virgülle ayrılmış)
    aciklama TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_personel FOREIGN KEY (personel_id) REFERENCES personel(id) ON DELETE CASCADE
);

-- Performans için indeksler
CREATE INDEX IF NOT EXISTS idx_vardiya_prog_personel ON personel_vardiya_programi(personel_id);
CREATE INDEX IF NOT EXISTS idx_vardiya_prog_tarih ON personel_vardiya_programi(baslangic_tarihi, bitis_tarihi);
