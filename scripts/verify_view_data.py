import sqlite3
import pandas as pd

def check_view_data():
    conn = sqlite3.connect('ekleristan_local.db')
    try:
        df = pd.read_sql("SELECT * FROM v_organizasyon_semasi", conn)
        print(f"View Row Count: {len(df)}")
        if not df.empty:
            print(df.head())
        else:
            print("View returned NO rows.")
            
            # Check raw personnel count for AKTİF
            count = pd.read_sql("SELECT count(*) FROM personnel WHERE durum = 'AKTİF'", conn).iloc[0][0]
            print(f"Actual 'AKTİF' personnel count: {count}")
            
    except Exception as e:
        print(f"Error reading view: {e}")
    conn.close()

if __name__ == "__main__":
    try:
        check_view_data()
    except Exception as e:
        print(f"Script Error: {e}")
