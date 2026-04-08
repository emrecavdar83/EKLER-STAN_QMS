-- v5.8.1: EKLERİSTAN QMS - Department System v2.0 Update
-- Tarih: 08.04.2026 | Adım 1: builder_db

-- 1. Departman Türleri Güncellemesi
ALTER TABLE IF EXISTS public.qms_departman_turleri 
ADD COLUMN IF NOT EXISTS kurallar_json TEXT, -- JSON formatında kısıtlama kuralları
ADD COLUMN IF NOT EXISTS durum TEXT DEFAULT 'AKTİF';

-- 2. Departmanlar Tablosu Güncellemesi
ALTER TABLE IF EXISTS public.qms_departmanlar 
ADD COLUMN IF NOT EXISTS ikincil_ust_id INTEGER, -- Matrix (2. Üst Birim)
ADD COLUMN IF NOT EXISTS yonetici_id INTEGER,    -- Sorumlu Yönetici
ADD COLUMN IF NOT EXISTS durum TEXT DEFAULT 'AKTİF';

-- 3. Veri Göçü (Madde 4: Silme Yasaktır, Durum Yönetimi)
-- Mevcut 'aktif' kolonundan verileri 'durum' kolonuna taşıyoruz.
DO $$ 
BEGIN 
    IF EXISTS (SELECT column_name FROM information_schema.columns WHERE table_name='qms_departmanlar' AND column_name='aktif') THEN
        UPDATE public.qms_departmanlar SET durum = CASE WHEN aktif = 1 THEN 'AKTİF' ELSE 'PASİF' END;
    END IF;
    
    IF EXISTS (SELECT column_name FROM information_schema.columns WHERE table_name='qms_departman_turleri' AND column_name='aktif') THEN
        UPDATE public.qms_departman_turleri SET durum = CASE WHEN aktif = 1 THEN 'AKTİF' ELSE 'PASİF' END;
    END IF;
END $$;

-- 4. Foreign Key Tanımlamaları (Referans Bütünlüğü)
ALTER TABLE IF EXISTS public.qms_departmanlar 
  ADD CONSTRAINT fk_ikincil_ust FOREIGN KEY (ikincil_ust_id) REFERENCES public.qms_departmanlar(id),
  ADD CONSTRAINT fk_yonetici FOREIGN KEY (yonetici_id) REFERENCES public.personel(id);

-- 5. Seed Data Enhancement (Üretim Birimleri İçin Varsayılan Kodlar)
UPDATE public.qms_departmanlar SET kod = 'UR-' || id WHERE ad LIKE '%ÜRETİM%' AND (kod IS NULL OR kod = '');
UPDATE public.qms_departmanlar SET kod = 'KL-' || id WHERE ad LIKE '%KALİTE%' AND (kod IS NULL OR kod = '');
UPDATE public.qms_departmanlar SET kod = 'DP-' || id WHERE ad LIKE '%DEPO%' AND (kod IS NULL OR kod = '');
UPDATE public.qms_departmanlar SET kod = 'OF-' || id WHERE ad LIKE '%OFİS%' AND (kod IS NULL OR kod = '');
