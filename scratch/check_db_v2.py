
import sqlite3
import pandas as pd
import sys

# Set encoding to utf-8 for windows console
sys.stdout.reconfigure(encoding='utf-8')

try:
    conn = sqlite3.connect('c:/Projeler/S_program/EKLER/ekleristan_local.db')
    
    # Query ayarlar_moduller
    df_mods = pd.read_sql_query("SELECT id, modul_anahtari, durum FROM ayarlar_moduller", conn)
    print("--- Modules (ayarlar_moduller) ---")
    print(df_mods.to_string())
    
    # Check if map_uretim specifically exists and its status
    map_check = pd.read_sql_query("SELECT * FROM ayarlar_moduller WHERE modul_anahtari = 'map_uretim'", conn)
    if not map_check.empty:
        print("\n--- MAP Module Status ---")
        print(map_check.to_string())
    else:
        print("\n--- MAP Module NOT FOUND in ayarlar_moduller ---")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
