import toml
from sqlalchemy import create_engine, text

def test_sql():
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["streamlit"]["DB_URL"]
    engine = create_engine(url)
    
    with engine.begin() as conn:
        print("Checking qdms_belgeler existence...")
        res = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'qdms_belgeler');")).scalar()
        print(f"qdms_belgeler exists in public: {res}")
        
        if not res:
            print("Attempting to CREATE TABLE qdms_belgeler directly...")
            conn.execute(text("""
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
                FOREIGN KEY (olusturan_id) REFERENCES personel(id)
            );
            """))
            print("Creation command executed.")
            res_after = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'qdms_belgeler');")).scalar()
            print(f"qdms_belgeler exists AFTER create: {res_after}")

if __name__ == "__main__":
    test_sql()
