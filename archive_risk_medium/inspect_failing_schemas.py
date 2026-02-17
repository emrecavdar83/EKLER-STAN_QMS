import sqlite3
import pandas as pd

def check_table_schema(table_name):
    try:
        conn = sqlite3.connect('ekleristan_local.db')
        cursor = conn.cursor()
        print(f"\n--- {table_name} Columns ---")
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        if not cols:
            print("Table not found!")
        for col in cols:
            # cid, name, type, notnull, dflt_value, pk
            is_pk = " (PK)" if col[5] else ""
            print(f"- {col[1]} [{col[2]}]{is_pk}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

tables_to_check = [
    "ayarlar_urunler",
    "tanim_metotlar",
    "tanim_ekipmanlar"
]

for table in tables_to_check:
    check_table_schema(table)
