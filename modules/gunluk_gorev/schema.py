from sqlalchemy import text
import streamlit as st

def _tablo_tanim_listesi(pk, ts, dt):
    return [
        f"""CREATE TABLE IF NOT EXISTS gunluk_gorev_katalogu (
            id {pk}, kod VARCHAR(50) UNIQUE, ad TEXT NOT NULL, kategori TEXT NOT NULL,
            aktif_mi INTEGER DEFAULT 1, aciklama TEXT, olusturma_tarihi {ts})""",
        f"""CREATE TABLE IF NOT EXISTS gunluk_periyodik_kurallar (
            id {pk}, personel_id INTEGER NOT NULL, kaynak_tipi TEXT NOT NULL,
            kaynak_id INTEGER, ad_ozel TEXT, oncelik TEXT DEFAULT 'NORMAL',
            periyot_tipi TEXT NOT NULL, periyot_detay TEXT DEFAULT '{{}}',
            aktif_mi INTEGER DEFAULT 1, olusturma_ts {ts})""",
        f"""CREATE TABLE IF NOT EXISTS birlesik_gorev_havuzu (
            id {pk}, personel_id INTEGER NOT NULL, bolum_id INTEGER,
            gorev_kaynagi TEXT NOT NULL, kaynak_id INTEGER, ad_ozel TEXT,
            v_tipi TEXT DEFAULT 'KATALOG', atanma_tarihi {dt} NOT NULL, hedef_tarih {dt} NOT NULL,
            durum TEXT DEFAULT 'BEKLIYOR', oncelik TEXT DEFAULT 'NORMAL', sapma_notu TEXT,
            tamamlanma_tarihi TIMESTAMP, atayan_id INTEGER, iptal_notu TEXT, iptal_eden_id INTEGER,
            UNIQUE(personel_id, hedef_tarih, gorev_kaynagi, kaynak_id, ad_ozel))""",
    ]


def _saha_mobil_hesap_garantile(engine):
    try:
        with engine.begin() as conn:
            r = conn.execute(text("SELECT COUNT(*) FROM ayarlar_kullanicilar WHERE kullanici_adi = 'Saha_Mobil'")).fetchone()
            if r[0] == 0:
                conn.execute(text("INSERT INTO ayarlar_kullanicilar (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye) VALUES ('SAHA MOBİL TERMİNAL', 'Saha_Mobil', 'mobil789', 'Personel', 'AKTİF', 5)"))
    except Exception as e:
        st.warning(f"⚠️ Saha_Mobil hesabı garanti edilemedi: {e}")


def init_gunluk_gorev_tables(engine):
    is_pg = engine.dialect.name == 'postgresql'
    pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    dt = "DATE" if is_pg else "TEXT"
    with engine.begin() as conn:
        for sql in _tablo_tanim_listesi(pk, ts, dt):
            try:
                conn.execute(text(sql))
            except Exception as e:
                st.error(f"❌ Veritabanı Tablo Hatası: {str(e)}"); raise e
    _saha_mobil_hesap_garantile(engine)
