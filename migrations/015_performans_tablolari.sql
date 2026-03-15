-- migrations/015_performans_tablolari.sql
-- SQLite ve Supabase PostgreSQL'de çalışacak şekilde yazılmıştır.
-- QMS Certification Gap: BRC v9 §7.1, IFS v8 §6.1 yetkinlik kaydı gereksinimini karşılar.

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS performans_degerledirme (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid                  TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    
    -- Personel bilgileri (FK yerine denormalize — audit trail için)
    personel_id           INTEGER,
    calisan_adi_soyadi    TEXT NOT NULL,
    bolum                 TEXT NOT NULL,
    gorevi                TEXT NOT NULL,
    ise_giris_tarihi      DATE,
    
    -- Dönem bilgisi
    donem                 TEXT NOT NULL CHECK(donem IN ('1. DÖNEM', '2. DÖNEM')),
    degerlendirme_tarihi  DATE NOT NULL,
    degerlendirme_yili    INTEGER NOT NULL,
    
    -- Mesleki Teknik Nitelikler (%70 ağırlık) — 8 kriter
    kkd_kullanimi         INTEGER CHECK(kkd_kullanimi BETWEEN 0 AND 100),
    mesleki_kriter_2      INTEGER CHECK(mesleki_kriter_2 BETWEEN 0 AND 100),
    mesleki_kriter_3      INTEGER CHECK(mesleki_kriter_3 BETWEEN 0 AND 100),
    mesleki_kriter_4      INTEGER CHECK(mesleki_kriter_4 BETWEEN 0 AND 100),
    mesleki_kriter_5      INTEGER CHECK(mesleki_kriter_5 BETWEEN 0 AND 100),
    mesleki_kriter_6      INTEGER CHECK(mesleki_kriter_6 BETWEEN 0 AND 100),
    mesleki_kriter_7      INTEGER CHECK(mesleki_kriter_7 BETWEEN 0 AND 100),
    mesleki_kriter_8      INTEGER CHECK(mesleki_kriter_8 BETWEEN 0 AND 100),
    mesleki_ortalama_puan REAL,     -- Python hesaplar, DB saklar
    
    -- Kurumsal Nitelikler (%30 ağırlık) — 8 kriter
    calisma_saatleri_uyum INTEGER CHECK(calisma_saatleri_uyum BETWEEN 0 AND 100),
    ogrenme_kabiliyeti    INTEGER CHECK(ogrenme_kabiliyeti BETWEEN 0 AND 100),
    iletisim_becerisi     INTEGER CHECK(iletisim_becerisi BETWEEN 0 AND 100),
    problem_cozme         INTEGER CHECK(problem_cozme BETWEEN 0 AND 100),
    kalite_bilinci        INTEGER CHECK(kalite_bilinci BETWEEN 0 AND 100),
    ise_baglilik_aidiyet  INTEGER CHECK(ise_baglilik_aidiyet BETWEEN 0 AND 100),
    ekip_calismasi_uyum   INTEGER CHECK(ekip_calismasi_uyum BETWEEN 0 AND 100),
    verimli_calisma       INTEGER CHECK(verimli_calisma BETWEEN 0 AND 100),
    kurumsal_ortalama_puan REAL,    -- Python hesaplar, DB saklar
    
    -- Sonuç
    agirlikli_toplam_puan REAL NOT NULL,  -- mesleki*0.70 + kurumsal*0.30
    polivalans_duzeyi     TEXT NOT NULL,  -- 5 kademeli metin sonucu
    polivalans_kodu       INTEGER NOT NULL CHECK(polivalans_kodu BETWEEN 1 AND 5),
    
    -- Yorum ve onay
    yorum                 TEXT,
    degerlendiren_adi     TEXT,
    
    -- Audit trail
    olusturma_tarihi      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncelleyen_kullanici TEXT,
    surum                 INTEGER DEFAULT 1,
    onceki_puan           REAL,
    
    -- Sync
    sync_durumu           TEXT DEFAULT 'bekliyor' CHECK(sync_durumu IN ('bekliyor','tamamlandi','hata')),
    silinmis              INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS polivalans_matris (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    personel_id      INTEGER,
    calisan_adi      TEXT NOT NULL,
    bolum            TEXT NOT NULL,
    gorevi           TEXT NOT NULL,
    guncelleme_yili  INTEGER NOT NULL,
    
    -- Son geçerli puanlar (en son iki dönem ortalaması)
    son_puan_d1      REAL,
    son_puan_d2      REAL,
    yil_ortalama     REAL,
    polivalans_kodu  INTEGER CHECK(polivalans_kodu BETWEEN 1 AND 5),
    polivalans_metni TEXT,
    
    -- Trend
    puan_degisimi    REAL,
    egitim_ihtiyaci  INTEGER DEFAULT 0,
    
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_durumu      TEXT DEFAULT 'bekliyor'
);

CREATE INDEX IF NOT EXISTS idx_perf_calisan ON performans_degerledirme(calisan_adi_soyadi);
CREATE INDEX IF NOT EXISTS idx_perf_bolum   ON performans_degerledirme(bolum);
CREATE INDEX IF NOT EXISTS idx_perf_donem   ON performans_degerledirme(donem, degerlendirme_yili);
CREATE INDEX IF NOT EXISTS idx_perf_sync    ON performans_degerledirme(sync_durumu);
CREATE INDEX IF NOT EXISTS idx_matris_cal   ON polivalans_matris(calisan_adi, guncelleme_yili);

COMMIT;
