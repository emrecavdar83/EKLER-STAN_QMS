-- Master Temizlik Planına Kat sütunu ekle
-- Supabase SQL Editor'da çalıştırın

-- Kat sütunu ekle (yoksa)
ALTER TABLE ayarlar_temizlik_plani 
ADD COLUMN IF NOT EXISTS kat TEXT;

-- Mevcut kayıtlarda kat boş olacak, daha sonra doldurabilirsiniz
-- Veya varsayılan bir değer atayabilirsiniz:
-- UPDATE ayarlar_temizlik_plani SET kat = 'KAT 1 - ÜRETİM' WHERE kat IS NULL;
