-- MANUAL ROLLBACK SCRIPT FOR QDMS NAV REFACTOR
-- Supabase SQL Editor üzerinden çalıştırılabilir.

BEGIN;

-- 1. Yeni 'qdms' modülünü ve yetkilerini sil
DELETE FROM public.ayarlar_moduller WHERE modul_anahtari = 'qdms';
DELETE FROM public.ayarlar_yetkiler WHERE modul_adi = 'qdms';

-- 2. Eski 4 modülü geri yükle
INSERT INTO public.ayarlar_moduller (modul_anahtari, modul_etiketi, aktif, sira_no) VALUES
('dokuman_merkezi', '📋 Doküman Merkezi', 1, 71),
('belge_yonetimi',  '⚙️ Belge Yönetimi',  1, 72),
('talimatlar',      '📖 Talimatlar',      1, 73),
('uyumluluk',       '✅ Uyumluluk',       1, 74)
ON CONFLICT (modul_anahtari) DO UPDATE SET aktif = 1;

-- 3. Temel Rol Yetkilerini Geri Yükle (Admin/Yönetim)
INSERT INTO public.ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES
('ADMIN', 'dokuman_merkezi', 'Düzenle'),
('ADMIN', 'belge_yonetimi',  'Düzenle'),
('ADMIN', 'talimatlar',      'Düzenle'),
('ADMIN', 'uyumluluk',       'Düzenle'),
('Yönetim Kurulu', 'dokuman_merkezi', 'Tam Yetki'),
('Yönetim Kurulu', 'belge_yonetimi',  'Görüntüle'),
('Yönetim Kurulu', 'talimatlar',      'Tam Yetki'),
('Yönetim Kurulu', 'uyumluluk',       'Tam Yetki'),
('Genel Müdür',    'dokuman_merkezi', 'Tam Yetki'),
('Genel Müdür',    'belge_yonetimi',  'Görüntüle'),
('Genel Müdür',    'talimatlar',      'Tam Yetki'),
('Genel Müdür',    'uyumluluk',       'Tam Yetki')
ON CONFLICT DO NOTHING;

COMMIT;
