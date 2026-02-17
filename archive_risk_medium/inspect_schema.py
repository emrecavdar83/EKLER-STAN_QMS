import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(personnel)")
    columns = cursor.fetchall()
    print("--- Personnel Table Columns ---")
    for col in columns:
        print(col)
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
