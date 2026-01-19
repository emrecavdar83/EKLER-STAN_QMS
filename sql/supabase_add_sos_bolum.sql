-- =====================================================
-- SOS BÖLÜMÜNÜ EKLE
-- =====================================================
-- Supabase SQL Editor'de çalıştırın
-- =====================================================

-- SOS bölümünü ekle
INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
SELECT 'SOS', TRUE, 10, 'Sos üretim bölümü'
WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'SOS');

-- Kontrol: Tüm bölümleri göster
SELECT bolum_adi, aktif, sira_no, aciklama
FROM ayarlar_bolumler
ORDER BY sira_no;

-- =====================================================
-- TAMAMLANDI
-- =====================================================
-- Streamlit Cloud'da reboot yapın
-- =====================================================
