import sqlite3
import pandas as pd

def check_depts():
    conn = sqlite3.connect('ekleristan_local.db')
    
    print("--- Mevcut Departmanlar (ayarlar_bolumler) ---")
    df = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", conn)
    print(df)
    
    print("\n--- Personel Departmanları (personel tablosu - bolum kolonu) ---")
    df_p = pd.read_sql("SELECT DISTINCT bolum FROM personel", conn)
    print(df_p)
    
    conn.close()

if __name__ == "__main__":
    check_depts()
