from scripts.sync_manager import SyncManager
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
sm = SyncManager()

try:
    with sm.local_engine.connect() as lconn:
        res = lconn.execute(text("SELECT * FROM sicaklik_olcumleri WHERE DATE(olcum_zamani) = '2026-02-28' LIMIT 1"))
        row = dict(res.fetchone()._mapping)
        print(f"Local Row found: {row}")

    # Remove ID for cloud insert
    del row['id']
    
    # Translate FKs
    row = sm._translate_row_fks('sicaklik_olcumleri', row, {})
    print(f"Translated Row: {row}")

    # Try Insert
    with sm.live_engine.begin() as cconn:
        cols = row.keys()
        placeholders = ", ".join([f":{c}" for c in cols])
        sql = text(f"INSERT INTO sicaklik_olcumleri ({', '.join(cols)}) VALUES ({placeholders})")
        print(f"Executing SQL: {sql}")
        cconn.execute(sql, row)
        print("--- PUSH SUCCESS ---")

except Exception as e:
    print(f"--- PUSH FAILED ---")
    print(f"Error Type: {type(e)}")
    print(f"Error Message: {e}")
