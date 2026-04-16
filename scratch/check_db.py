
import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('c:/Projeler/S_program/EKLER/ekleristan_local.db')
    print("--- Modules (ayarlar_moduller) ---")
    df_mods = pd.read_sql_query("SELECT * FROM ayarlar_moduller", conn)
    print(df_mods)
    
    print("\n--- Permissions for ADMIN (ayarlar_yetkiler) ---")
    df_yetki = pd.read_sql_query("SELECT * FROM ayarlar_yetkiler WHERE rol_adi = 'ADMIN' AND modul_adi LIKE '%map%'", conn)
    print(df_yetki)
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
