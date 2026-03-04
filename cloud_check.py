import toml
import os
import sqlalchemy
from sqlalchemy import text
from datetime import date, datetime, timedelta
import pandas as pd

def check_cloud_data():
    secrets_path = os.path.join(os.path.dirname(__file__), "secrets.toml")
    if not os.path.exists(".streamlit/secrets.toml"):
        print("secrets.toml not found in current dir, please run from EKLERİSTAN_QMS")
        return

    s = toml.load(".streamlit/secrets.toml")
    url = s.get('streamlit', {}).get('DB_URL', s.get('DB_URL'))
    url = url[1:-1] if url.startswith('"') else url
    
    engine = sqlalchemy.create_engine(url)
    target_date = date(2026, 2, 28)
    
    with engine.connect() as conn:
        print(f"--- DB CHECK FOR {target_date} ---")
        
        # 1. Check if rooms exist
        rooms = pd.read_sql(text("SELECT id, oda_adi FROM soguk_odalar"), conn)
        print(f"\nRooms Total: {len(rooms)}")
        
        # 2. Check Plan
        s_dt = datetime.combine(target_date, datetime.min.time())
        e_dt = s_dt + timedelta(days=1)
        plan = pd.read_sql(text("SELECT oda_id, beklenen_zaman, durum, gerceklesen_olcum_id FROM olcum_plani WHERE beklenen_zaman >= :s AND beklenen_zaman < :e"), conn, params={"s": s_dt, "e": e_dt})
        print(f"\nPlans for {target_date}: {len(plan)}")
        if not plan.empty: print(plan.head())
        
        # 3. Check Measurements
        measurements = pd.read_sql(text("SELECT oda_id, olcum_zamani, sicaklik_degeri, planlanan_zaman FROM sicaklik_olcumleri WHERE olcum_zamani >= :s AND olcum_zamani < :e"), conn, params={"s": s_dt, "e": e_dt})
        print(f"\nMeasurements for {target_date}: {len(measurements)}")
        if not measurements.empty: print(measurements.head())

if __name__ == "__main__":
    check_cloud_data()
