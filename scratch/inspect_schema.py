
import sqlite3
import pandas as pd
import sys

# Set encoding to utf-8 for windows console
sys.stdout.reconfigure(encoding='utf-8')

try:
    conn = sqlite3.connect('c:/Projeler/S_program/EKLER/ekleristan_local.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("--- Tables in Database ---")
    for table in tables:
        print(f"Table: {table[0]}")
        # Get columns for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    # Also check content of ayarlar_moduller with available columns
    print("\n--- Content of ayarlar_moduller ---")
    df_mods = pd.read_sql_query("SELECT * FROM ayarlar_moduller", conn)
    print(df_mods.to_string())
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
