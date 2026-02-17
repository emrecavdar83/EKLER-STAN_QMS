
import sqlite3
import pandas as pd

def inspect_local():
    conn = sqlite3.connect('ekleristan_local.db')
    
    print("\n--- AYARLAR_BOLUMLER (Local) ---")
    df_bolumler = pd.read_sql("SELECT * FROM ayarlar_bolumler ORDER BY sira_no", conn)
    print(df_bolumler)
    
    print("\n--- AYARLAR_ROLLER (Local) ---")
    df_roller = pd.read_sql("SELECT * FROM ayarlar_roller", conn)
    print(df_roller)
    
    conn.close()

if __name__ == "__main__":
    inspect_local()
