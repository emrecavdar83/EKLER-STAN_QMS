import toml
import os
import sqlalchemy
from sqlalchemy import text
from datetime import date, datetime, timedelta
import pandas as pd

def check_databases():
    secrets_path = ".streamlit/secrets.toml"
    s = toml.load(secrets_path)
    
    # 1. Cloud URL
    cloud_url = s.get('streamlit', {}).get('DB_URL', s.get('DB_URL'))
    cloud_url = cloud_url[1:-1] if cloud_url.startswith('"') else cloud_url
    
    # 2. Local URL
    local_url = "sqlite:///ekleristan_local.db"
    
    target_date = date(2026, 2, 28)
    s_dt = datetime.combine(target_date, datetime.min.time())
    e_dt = s_dt + timedelta(days=1)
    
    for name, url in [("LOCAL (SQLite)", local_url), ("CLOUD (Postgres)", cloud_url)]:
        print(f"\n==========================================")
        print(f"CHECKING {name}")
        print(f"==========================================")
        try:
            engine = sqlalchemy.create_engine(url)
            with engine.connect() as conn:
                # Measurements
                query = text("SELECT COUNT(*) FROM sicaklik_olcumleri WHERE olcum_zamani >= :s AND olcum_zamani < :e")
                m_count = conn.execute(query, {"s": s_dt, "e": e_dt}).scalar()
                
                # Plans
                p_query = text("SELECT COUNT(*) FROM olcum_plani WHERE beklenen_zaman >= :s AND beklenen_zaman < :e")
                p_count = conn.execute(p_query, {"s": s_dt, "e": e_dt}).scalar()
                
                # Today's Production
                prod_query = text("SELECT COUNT(*) FROM depo_giris_kayitlari WHERE tarih = :t")
                prod_count = conn.execute(prod_query, {"t": str(target_date)}).scalar()

                print(f"Cold Room Measurements (Today): {m_count}")
                print(f"Cold Room Plans (Today): {p_count}")
                print(f"Production Records (Today): {prod_count}")
                
        except Exception as e:
            print(f"Error checking {name}: {e}")

if __name__ == "__main__":
    check_databases()
