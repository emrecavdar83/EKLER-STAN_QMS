-- =====================================================
-- PERSONEL TABLOSUNU TEMİZLE (TÜM KAYITLARI SİL)
-- =====================================================
-- ⚠️ DİKKAT: Bu işlem GERİ ALINAMAZ!
-- ⚠️ Tüm personel kayıtları silinecek
-- =====================================================

-- Önce kaç kayıt olduğunu görelim
SELECT COUNT(*) as toplam_personel FROM personel;

-- ⚠️ ONAY: Aşağıdaki satırı çalıştırmadan önce emin olun!
-- Tüm personel kayıtlarını sil
DELETE FROM personel;

-- Kontrol: Tablo boş mu?
SELECT COUNT(*) as kalan_kayit FROM personel;

-- =====================================================
-- TAMAMLANDI - PERSONEL TABLOSU TEMİZLENDİ
-- =====================================================
-- Şimdi uygulamadan yeni personelleri ekleyebilirsiniz
-- Ayarlar → Personel sekmesinden tek tek ekleyin
-- =====================================================
