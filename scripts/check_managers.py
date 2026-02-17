import sqlite3
import pandas as pd

def check_managers():
    conn = sqlite3.connect('ekleristan_local.db')
    try:
        count_assigned = pd.read_sql("SELECT count(*) FROM personnel WHERE yonetici_id > 0", conn).iloc[0][0]
        print(f"Personel with Manager Assigned (yonetici_id > 0): {count_assigned}")
        
        df = pd.read_sql("SELECT id, ad_soyad, bolum, yonetici_id FROM personnel LIMIT 10", conn)
        print(df.to_string(index=False))
        
    except Exception as e:
        print(f"Error: {e}")
    conn.close()

if __name__ == "__main__":
    check_managers()
