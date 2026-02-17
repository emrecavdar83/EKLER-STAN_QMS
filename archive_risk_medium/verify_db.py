
import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('ekleristan_local.db')
    query = "SELECT id, ad_soyad, durum, vardiya FROM personnel WHERE ad_soyad LIKE '%AHMAD KOURANI%'"
    df = pd.read_sql(query, conn)
    print("--- VERITABANI SORGUSU SONUCU ---")
    print(df)
    conn.close()
except Exception as e:
    print(e)
