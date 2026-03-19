-- EKLERİSTAN QMS - QDMS Modülü Migration
-- Tarih: 18.03.2026
-- 13. Adam Protokolü: personel(id) referanslı

CREATE TABLE IF NOT EXISTS public.qdms_belgeler (
    id                  SERIAL PRIMARY KEY,
    belge_kodu          TEXT NOT NULL UNIQUE,
    belge_adi           TEXT NOT NULL,
    belge_tipi          TEXT NOT NULL,
    alt_kategori        TEXT,
    aktif_rev           INTEGER NOT NULL DEFAULT 1,
    durum               TEXT NOT NULL DEFAULT 'taslak',
    olusturan_id        INTEGER,
    olusturma_tarihi    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleme_tarihi   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aciklama            TEXT,
    FOREIGN KEY (olusturan_id) REFERENCES public.personel(id)
);

CREATE TABLE IF NOT EXISTS public.qdms_sablonlar (
    id                  SERIAL PRIMARY KEY,
    belge_kodu          TEXT NOT NULL,
    rev_no              INTEGER NOT NULL DEFAULT 1,
    header_config       TEXT NOT NULL,
    kolon_config        TEXT NOT NULL,
    meta_panel_config   TEXT,
    sayfa_boyutu        TEXT DEFAULT 'A4',
    sayfa_yonu          TEXT DEFAULT 'dikey',
    renk_tema           TEXT,
    css_ek              TEXT,
    aktif               INTEGER DEFAULT 1,
    olusturma_tarihi    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (belge_kodu) REFERENCES public.qdms_belgeler(belge_kodu),
    UNIQUE (belge_kodu, rev_no)
);

CREATE TABLE IF NOT EXISTS public.qdms_revizyon_log (
    id                  SERIAL PRIMARY KEY,
    belge_kodu          TEXT NOT NULL,
    eski_rev            INTEGER,
    yeni_rev            INTEGER NOT NULL,
    degisiklik_notu     TEXT NOT NULL,
    degistiren_id       INTEGER,
    degisiklik_tarihi   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    degisiklik_tipi     TEXT,
    FOREIGN KEY (belge_kodu) REFERENCES public.qdms_belgeler(belge_kodu),
    FOREIGN KEY (degistiren_id) REFERENCES public.personel(id)
);

CREATE TABLE IF NOT EXISTS public.qdms_yayim (
    id                  SERIAL PRIMARY KEY,
    belge_kodu          TEXT NOT NULL,
    rev_no              INTEGER NOT NULL,
    yayim_tarihi        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    iptal_tarihi        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    yayimlayan_id       INTEGER,
    lokasyon_kapsam     TEXT DEFAULT 'tum',
    yayim_notu          TEXT,
    FOREIGN KEY (belge_kodu) REFERENCES public.qdms_belgeler(belge_kodu),
    FOREIGN KEY (yayimlayan_id) REFERENCES public.personel(id)
);

CREATE TABLE IF NOT EXISTS public.qdms_talimatlar (
    id                  SERIAL PRIMARY KEY,
    talimat_kodu        TEXT NOT NULL UNIQUE,
    belge_kodu          TEXT,
    talimat_adi         TEXT NOT NULL,
    talimat_tipi        TEXT NOT NULL,
    ekipman_id          INTEGER,
    departman           TEXT,
    adimlar_json        TEXT,
    gorsel_url          TEXT,
    qr_token            TEXT UNIQUE,
    aktif               INTEGER DEFAULT 1,
    rev_no              INTEGER DEFAULT 1,
    olusturma_tarihi    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (belge_kodu) REFERENCES public.qdms_belgeler(belge_kodu)
);

CREATE TABLE IF NOT EXISTS public.qdms_okuma_onay (
    id                  SERIAL PRIMARY KEY,
    belge_kodu          TEXT NOT NULL,
    rev_no              INTEGER NOT NULL,
    personel_id         INTEGER NOT NULL,
    okuma_tarihi        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    onay_tipi           TEXT DEFAULT 'manuel',
    cihaz_bilgisi       TEXT,
    FOREIGN KEY (belge_kodu) REFERENCES public.qdms_belgeler(belge_kodu),
    FOREIGN KEY (personel_id) REFERENCES public.personel(id)
);

-- BOOTSTRAP: QDMS Modül ve Yetki Tanımları
-- BOOTSTRAP: QDMS Konsolide Modül Tanımı (Madde 16)
INSERT INTO public.ayarlar_moduller (modul_anahtari, modul_etiketi, aktif, sira_no) VALUES
('qdms', '📁 QDMS', 1, 71)
ON CONFLICT (modul_anahtari) DO UPDATE SET aktif = 1, sira_no = 71;

-- YETKİLER: Yönetim ve Kalite (Düzenle/Tam Yetki - Sidebar Görünürlüğü)
INSERT INTO public.ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES
('ADMIN',            'qdms', 'Düzenle'),
('Yönetim Kurulu',   'qdms', 'Düzenle'),
('Genel Müdür',      'qdms', 'Düzenle'),
('KALİTE',           'qdms', 'Düzenle'),
('Müdürler',          'qdms', 'Düzenle'),
('Direktörler',       'qdms', 'Düzenle'),
('Bölüm Sorumlusu',   'qdms', 'Görüntüle'),
('Koordinatör / Şef', 'qdms', 'Görüntüle'),
('Personel',          'qdms', 'Görüntüle'),
('Stajyer/Geçici',    'qdms', 'Görüntüle')
ON CONFLICT (rol_adi, modul_adi) DO UPDATE SET erisim_turu = EXCLUDED.erisim_turu;
