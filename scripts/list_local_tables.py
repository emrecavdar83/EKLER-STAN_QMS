import sqlite3
import pandas as pd

def list_local_tables(db_path='ekleristan_local.db'):
    print(f"--- Lokal Veritabanı Tablo Listesi ({db_path}) ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            t_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {t_name}")
            count = cursor.fetchone()[0]
            print(f"- {t_name} ({count} kayıt)")
        conn.close()
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    list_local_tables()
