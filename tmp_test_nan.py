from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        print("Testing NaN update on integer column...")
        # nan is float(nan)
        val = np.nan
        sql = text("UPDATE personel SET yonetici_id = :y WHERE id = 16")
        conn.execute(sql, {"y": val})
        print("Success (Surprisingly)")
except Exception as e:
    print(f"Error caught: {e}")
