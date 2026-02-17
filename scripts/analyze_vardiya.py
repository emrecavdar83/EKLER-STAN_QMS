import sqlite3
import pandas as pd

def analyze():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    print("--- Tablolarda Vardiya Kolon Sorgusu ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    for table in tables:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [c[1] for c in cursor.fetchall()]
            if 'vardiya' in columns:
                print(f"\nTablo: {table}")
                df = pd.read_sql(f"SELECT distinct vardiya, count(*) as adet FROM {table} GROUP BY vardiya", conn)
                print(df)
        except Exception as e:
            print(f"Hata ({table}): {e}")
            
    conn.close()

if __name__ == "__main__":
    analyze()
