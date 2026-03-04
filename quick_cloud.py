import toml
import os
import sqlalchemy
from sqlalchemy import text
from datetime import date, datetime, timedelta
import pandas as pd

def check_cloud_quick():
    secrets_path = ".streamlit/secrets.toml"
    s = toml.load(secrets_path)
    
    # Cloud URL
    url = s.get('streamlit', {}).get('DB_URL', s.get('DB_URL'))
    url = url[1:-1] if url.startswith('"') else url
    
    # Safe range filter logic exactly as applied in the UI
    target_date = date(2026, 2, 28)
    s_dt = datetime.combine(target_date, datetime.min.time())
    e_dt = s_dt + timedelta(days=1)
    s_str = s_dt.strftime('%Y-%m-%d %H:%M:%S')
    e_str = e_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Increase connection timeout just in case DB is waking up
        engine = sqlalchemy.create_engine(url, connect_args={"connect_timeout": 30})
        with engine.connect() as conn:
            # Measurements exactly as in ui
            query = text("SELECT COUNT(*) FROM sicaklik_olcumleri WHERE olcum_zamani >= :s AND olcum_zamani < :e")
            m_count = conn.execute(query, {"s": s_str, "e": e_str}).scalar()
            
            # Data preview
            raw_query = text("SELECT oda_id, sicaklik_degeri, olcum_zamani FROM sicaklik_olcumleri WHERE olcum_zamani >= :s AND olcum_zamani < :e LIMIT 2")
            preview = conn.execute(raw_query, {"s": s_str, "e": e_str}).fetchall()
                
            print(f"--- SUCCESS: CLOUD CONNECTION OK ---")
            print(f"Cloud Measurements count with SAFE filter: {m_count}")
            print(f"Preview: {preview}")
            
    except Exception as e:
        print(f"Error checking cloud: {e}")

if __name__ == "__main__":
    check_cloud_quick()
