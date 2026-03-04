from scripts.sync_manager import SyncManager
from sqlalchemy import text
import pandas as pd

sm = SyncManager()

def push_today():
    tables = ["sicaklik_olcumleri", "olcum_plani"]
    for table in tables:
        col_date = "olcum_zamani" if table == "sicaklik_olcumleri" else "beklenen_zaman"
        
        with sm.local_engine.connect() as lconn:
            rows = [dict(r._mapping) for r in lconn.execute(text(f"SELECT * FROM {table} WHERE DATE({col_date}) = '2026-02-28'")).fetchall()]

        print(f"\n--- Processing TABLE: {table} ({len(rows)} rows) ---")
        
        # Build maps
        fk_maps = {}
        if table in sm.fk_map:
            for col, (ref_table, logical_key) in sm.fk_map[table].items():
                map_key = f"{ref_table}_{logical_key}"
                fk_maps[map_key] = sm._get_id_map(ref_table, logical_key)

        success_count = 0
        for row in rows:
            row.pop('id', None)
            row = sm._translate_row_fks(table, row, fk_maps)
            
            try:
                with sm.live_engine.begin() as cconn:
                    cols = list(row.keys())
                    sql = text(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join([':'+c for c in cols])})")
                    cconn.execute(sql, row)
                    success_count += 1
            except Exception as e:
                # Silently skip duplicates but print others
                if "duplicate key" not in str(e).lower():
                    print(f"FAILED {row.get(col_date)}: {e}")
        
        print(f"Result for {table}: {success_count}/{len(rows)} NEW records pushed.")

if __name__ == "__main__":
    push_today()
