
import sqlalchemy
from sqlalchemy import text, create_engine
import toml
import pandas as pd

def check_planning():
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("--- Cold Rooms Status ---")
        rooms = pd.read_sql(text("SELECT id, oda_adi, olcum_sikligi, ozel_olcum_saatleri, durum FROM soguk_odalar"), conn)
        print(rooms)
        
        print("\n--- Recent Planning Slots (Last 24h to future) ---")
        plan = pd.read_sql(text("""
            SELECT p.id, o.oda_adi, p.beklenen_zaman, p.durum, p.gerceklesen_olcum_id 
            FROM olcum_plani p
            JOIN soguk_odalar o ON p.oda_id = o.id
            WHERE p.beklenen_zaman > current_date - interval '1 day'
            ORDER BY o.oda_adi, p.beklenen_zaman ASC
        """), conn)
        print(plan)

if __name__ == "__main__":
    check_planning()
