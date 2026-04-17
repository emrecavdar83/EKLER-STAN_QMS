from sqlalchemy import text
import streamlit as st

def init_gunluk_gorev_tables(engine):
    """
    Günlük Görevler modülü için gerekli tabloları senkronize eder.
    Hataları yutmaz, ekrana basar.
    """
    is_pg = engine.dialect.name == 'postgresql'
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    _dt = "DATE" if is_pg else "TEXT"
    
    tables = [
        # 1. gunluk_gorev_katalogu
        f"""
        CREATE TABLE IF NOT EXISTS gunluk_gorev_katalogu (
            id          {_pk},
            kod         VARCHAR(50) UNIQUE,
            ad          TEXT NOT NULL,
            kategori    TEXT NOT NULL,
            aktif_mi    INTEGER DEFAULT 1,
            aciklama    TEXT,
            olusturma_tarihi {_ts}
        )
        """,
        # 2. gunluk_periyodik_kurallar
        f"""
        CREATE TABLE IF NOT EXISTS gunluk_periyodik_kurallar (
            id          {_pk},
            personel_id INTEGER NOT NULL,
            kaynak_tipi TEXT NOT NULL, -- KATALOG, AD-HOC
            kaynak_id   INTEGER, -- NULL if AD-HOC
            ad_ozel     TEXT,
            oncelik     TEXT DEFAULT 'NORMAL',
            periyot_tipi TEXT NOT NULL, -- GUNLUK, HAFTALIK, AYLIK, YILLIK
            periyot_detay TEXT DEFAULT '{{}}',
            aktif_mi    INTEGER DEFAULT 1,
            olusturma_ts {_ts}
        )
        """,
        # 3. birlesik_gorev_havuzu
        f"""
        CREATE TABLE IF NOT EXISTS birlesik_gorev_havuzu (
            id          {_pk},
            personel_id INTEGER NOT NULL,
            bolum_id    INTEGER,
            gorev_kaynagi TEXT NOT NULL, -- PERIYODIK, MANUEL, QDMS
            kaynak_id   INTEGER,
            ad_ozel     TEXT,
            v_tipi      TEXT DEFAULT 'KATALOG', -- KATALOG, AD-HOC
            atanma_tarihi {_dt} NOT NULL,
            hedef_tarih   {_dt} NOT NULL,
            durum       TEXT DEFAULT 'BEKLIYOR', -- BEKLIYOR, TAMAMLANDI, IPTAL
            oncelik     TEXT DEFAULT 'NORMAL',
            sapma_notu  TEXT,
            tamamlanma_tarihi TIMESTAMP,
            atayan_id   INTEGER,
            iptal_notu  TEXT,
            iptal_eden_id INTEGER,
            UNIQUE(personel_id, hedef_tarih, gorev_kaynagi, kaynak_id, ad_ozel)
        )
        """
    ]
    
    # PG için AUTOCOMMIT modunda çalıştırılması önerilir (DDL için)
    # get_engine() zaten maint_eng ile buraya paslayacak
    
    # 1. Tabloları oluştur
    with engine.begin() as conn:
        for sql in tables:
            try:
                conn.execute(text(sql))
            except Exception as e:
                st.error(f"❌ Veritabanı Tablo Hatası: {str(e)}")
                raise e
    
    # 2. Saha_Mobil Hesabı
    try:
        with engine.begin() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM ayarlar_kullanicilar WHERE kullanici_adi = 'Saha_Mobil'")).fetchone()
            if res[0] == 0:
                conn.execute(text("""
                    INSERT INTO ayarlar_kullanicilar (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye)
                    VALUES ('SAHA MOBİL TERMİNAL', 'Saha_Mobil', 'mobil789', 'Personel', 'AKTİF', 5)
                """))
    except Exception as e:
        st.warning(f"⚠️ Saha_Mobil hesabı garanti edilemedi: {e}")
