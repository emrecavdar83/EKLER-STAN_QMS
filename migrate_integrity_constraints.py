
import sqlite3
from sqlalchemy import create_engine, text
import toml
import os

def get_engine_live():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        url = secrets.get("DB_URL") or (secrets.get("streamlit", {}).get("DB_URL"))
        if url:
            if url.startswith('"'): url = url[1:-1]
            return create_engine(url)
    return None

def migrate_live():
    print("--- Migrating LIVE (Postgres) ---")
    engine = get_engine_live()
    if not engine:
        print("Live engine not found.")
        return
        
    with engine.begin() as conn:
        try:
            print("Adding UNIQUE to ayarlar_bolumler.bolum_adi...")
            conn.execute(text("ALTER TABLE ayarlar_bolumler DROP CONSTRAINT IF EXISTS unique_bolum_adi"))
            conn.execute(text("ALTER TABLE ayarlar_bolumler ADD CONSTRAINT unique_bolum_adi UNIQUE (bolum_adi)"))
            print("Done.")
        except Exception as e:
            print(f"Error migrating ayarlar_bolumler on LIVE: {e}")

        try:
            print("Adding UNIQUE to personel.kullanici_adi...")
            conn.execute(text("ALTER TABLE personel DROP CONSTRAINT IF EXISTS unique_kullanici_adi"))
            conn.execute(text("ALTER TABLE personel ADD CONSTRAINT unique_kullanici_adi UNIQUE (kullanici_adi)"))
            print("Done.")
        except Exception as e:
            print(f"Error migrating personel on LIVE: {e}")

def migrate_local():
    print("--- Migrating LOCAL (SQLite) ---")
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # SQLite requires table recreation for UNIQUE constraint on existing columns
    
    # 1. ayarlar_bolumler
    try:
        print("Recreating ayarlar_bolumler in LOCAL...")
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("ALTER TABLE ayarlar_bolumler RENAME TO ayarlar_bolumler_old")
        cursor.execute("""
            CREATE TABLE ayarlar_bolumler (
                id FLOAT,
                bolum_adi TEXT UNIQUE,
                aciklama TEXT,
                aktif BOOLEAN,
                olusturma_tarihi TEXT,
                sira_no BIGINT,
                ana_departman_id FLOAT,
                tur TEXT,
                guncelleme_tarihi TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO ayarlar_bolumler (id, bolum_adi, aciklama, aktif, olusturma_tarihi, sira_no, ana_departman_id, tur, guncelleme_tarihi)
            SELECT id, bolum_adi, aciklama, aktif, olusturma_tarihi, sira_no, ana_departman_id, tur, guncelleme_tarihi
            FROM ayarlar_bolumler_old
        """)
        cursor.execute("DROP TABLE ayarlar_bolumler_old")
        conn.commit()
        print("Done.")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating ayarlar_bolumler on LOCAL: {e}")

    # 2. personel
    try:
        print("Recreating personel in LOCAL...")
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("ALTER TABLE personel RENAME TO personel_old")
        cursor.execute("""
            CREATE TABLE personel (
                ad_soyad TEXT,
                kullanici_adi TEXT UNIQUE,
                sifre TEXT,
                rol TEXT,
                gorev TEXT,
                durum TEXT,
                ise_giris_tarihi TEXT,
                izin_gunu TEXT,
                id BIGINT,
                departman_id FLOAT,
                yonetici_id FLOAT,
                pozisyon_seviye BIGINT,
                is_cikis_tarihi TEXT,
                ayrilma_sebebi TEXT,
                bolum TEXT,
                sorumlu_bolum TEXT,
                kat TEXT,
                telefon_no TEXT,
                servis_duragi TEXT,
                guncelleme_tarihi TIMESTAMP,
                vardiya TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, gorev, durum, ise_giris_tarihi, izin_gunu, id, departman_id, yonetici_id, pozisyon_seviye, is_cikis_tarihi, ayrilma_sebebi, bolum, sorumlu_bolum, kat, telefon_no, servis_duragi, guncelleme_tarihi, vardiya)
            SELECT ad_soyad, kullanici_adi, sifre, rol, gorev, durum, ise_giris_tarihi, izin_gunu, id, departman_id, yonetici_id, pozisyon_seviye, is_cikis_tarihi, ayrilma_sebebi, bolum, sorumlu_bolum, kat, telefon_no, servis_duragi, guncelleme_tarihi, vardiya
            FROM personel_old
        """)
        cursor.execute("DROP TABLE personel_old")
        conn.commit()
        print("Done.")
    except Exception as e:
        conn.rollback()
        print(f"Error migrating personel on LOCAL: {e}")

    conn.close()

if __name__ == "__main__":
    print("STARTING MIGRATION PROCESS")
    try:
        migrate_local()
        print("LOCAL MIGRATION FINISHED")
        migrate_live()
        print("LIVE MIGRATION FINISHED")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    print("MIGRATION PROCESS ENDED")
