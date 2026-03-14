import toml
from sqlalchemy import create_engine, text

def migrate():
    s = toml.load(".streamlit/secrets.toml")
    url = s.get('streamlit', {}).get('DB_URL', s.get('DB_URL', '')).strip('"')
    engine = create_engine(url)
    
    with engine.begin() as conn:
        print("Migrating Cloud DB...")
        # Add film_tipi if not exists
        conn.execute(text("ALTER TABLE map_bobin_kaydi ADD COLUMN IF NOT EXISTS film_tipi TEXT"))
        # Add KG columns if not exists
        conn.execute(text("ALTER TABLE map_bobin_kaydi ADD COLUMN IF NOT EXISTS baslangic_kg NUMERIC(10,2)"))
        conn.execute(text("ALTER TABLE map_bobin_kaydi ADD COLUMN IF NOT EXISTS bitis_kg NUMERIC(10,2)"))
        conn.execute(text("ALTER TABLE map_bobin_kaydi ADD COLUMN IF NOT EXISTS kullanilan_kg NUMERIC(10,2)"))
        print("Cloud DB migration successful.")

    # Local SQLite
    try:
        import sqlite3
        conn_l = sqlite3.connect("ekleristan_local.db")
        print("Migrating Local DB...")
        # Check if column exists
        cols = [r[1] for r in conn_l.execute("PRAGMA table_info(map_bobin_kaydi)").fetchall()]
        if 'film_tipi' not in cols:
            conn_l.execute("ALTER TABLE map_bobin_kaydi ADD COLUMN film_tipi TEXT")
        if 'baslangic_kg' not in cols:
            conn_l.execute("ALTER TABLE map_bobin_kaydi ADD COLUMN baslangic_kg REAL")
        if 'bitis_kg' not in cols:
            conn_l.execute("ALTER TABLE map_bobin_kaydi ADD COLUMN bitis_kg REAL")
        if 'kullanilan_kg' not in cols:
            conn_l.execute("ALTER TABLE map_bobin_kaydi ADD COLUMN kullanilan_kg REAL")
        conn_l.commit()
        conn_l.close()
        print("Local DB migration successful.")
    except Exception as e:
        print(f"Local DB error: {e}")

if __name__ == "__main__":
    migrate()
