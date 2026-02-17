-- Supabase'de sıklık constraint'ini güncelle (Her Vardiya ekle)
-- Bu komutu Supabase SQL Editor'da çalıştırın

-- Mevcut constraint'i kaldır
ALTER TABLE lokasyon_proses_atama DROP CONSTRAINT IF EXISTS lokasyon_proses_atama_siklik_check;

-- Yeni constraint ekle (Her Vardiya dahil)
ALTER TABLE lokasyon_proses_atama 
ADD CONSTRAINT lokasyon_proses_atama_siklik_check 
CHECK (siklik IN ('Her Vardiya', 'Her Kullanım', 'Günlük', 'Haftalık', 'Aylık', '3 Aylık', 'Yıllık'));

-- Doğrulama: Constraint'leri listele
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'lokasyon_proses_atama'::regclass;
