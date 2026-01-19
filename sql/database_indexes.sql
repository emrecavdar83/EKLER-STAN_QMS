-- Ekleristan QMS Performans İyileştirme İndeksleri
-- Bu indeksler sadece OKUMA hızını artırır, hiçbir veriyi değiştirmez

-- 1. Personel Tablosu İndeksleri
CREATE INDEX IF NOT EXISTS idx_personel_kullanici_adi ON personel(kullanici_adi);
CREATE INDEX IF NOT EXISTS idx_personel_bolum ON personel(bolum);
CREATE INDEX IF NOT EXISTS idx_personel_vardiya ON personel(vardiya);
CREATE INDEX IF NOT EXISTS idx_personel_durum ON personel(durum);
CREATE INDEX IF NOT EXISTS idx_personel_bolum_vardiya ON personel(bolum, vardiya);

-- 2. Depo Giriş Kayıtları İndeksleri
CREATE INDEX IF NOT EXISTS idx_depo_tarih ON depo_giris_kayitlari(tarih);
CREATE INDEX IF NOT EXISTS idx_depo_urun ON depo_giris_kayitlari(urun);
CREATE INDEX IF NOT EXISTS idx_depo_tarih_urun ON depo_giris_kayitlari(tarih, urun);

-- 3. Ürün KPI Kontrol İndeksleri
CREATE INDEX IF NOT EXISTS idx_kpi_tarih ON urun_kpi_kontrol(tarih);
CREATE INDEX IF NOT EXISTS idx_kpi_urun ON urun_kpi_kontrol(urun);
CREATE INDEX IF NOT EXISTS idx_kpi_karar ON urun_kpi_kontrol(karar);
CREATE INDEX IF NOT EXISTS idx_kpi_tarih_urun ON urun_kpi_kontrol(tarih, urun);

-- 4. Hijyen Kontrol Kayıtları İndeksleri
CREATE INDEX IF NOT EXISTS idx_hijyen_tarih ON hijyen_kontrol_kayitlari(tarih);
CREATE INDEX IF NOT EXISTS idx_hijyen_bolum ON hijyen_kontrol_kayitlari(bolum);
CREATE INDEX IF NOT EXISTS idx_hijyen_tarih_bolum ON hijyen_kontrol_kayitlari(tarih, bolum);

-- 5. Temizlik Kayıtları İndeksleri
CREATE INDEX IF NOT EXISTS idx_temizlik_tarih ON temizlik_kayitlari(tarih);
CREATE INDEX IF NOT EXISTS idx_temizlik_bolum ON temizlik_kayitlari(bolum);
CREATE INDEX IF NOT EXISTS idx_temizlik_tarih_bolum ON temizlik_kayitlari(tarih, bolum);

-- 6. Temizlik Planı İndeksleri
CREATE INDEX IF NOT EXISTS idx_plan_kat_bolum ON ayarlar_temizlik_plani(kat_bolum);
CREATE INDEX IF NOT EXISTS idx_plan_yer_ekipman ON ayarlar_temizlik_plani(yer_ekipman);

-- Doğrulama: İndekslerin oluşturulduğunu kontrol et
-- SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;
