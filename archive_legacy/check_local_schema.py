import sqlite3
import pandas as pd

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(personel)")
cols = cursor.fetchall()
print("--- LOCAL PERSONEL COLUMNS ---")
for col in cols:
    print(f"- {col[1]}")
conn.close()
