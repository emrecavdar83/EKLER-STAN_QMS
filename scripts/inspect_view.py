from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine('sqlite:///ekleristan_local.db')

def inspect_view():
    print("--- VIEW INSPECTION ---")
    try:
        with engine.connect() as conn:
            # 1. View Definition
            res = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='view' AND name='v_organizasyon_semasi'")).fetchone()
            if res:
                print(f"SQL: {res[0]}")
            else:
                print("View 'v_organizasyon_semasi' NOT FOUND.")
                
            # 2. View Content Columns
            try:
                df = pd.read_sql("SELECT * FROM v_organizasyon_semasi LIMIT 1", conn)
                print(f"Columns: {df.columns.tolist()}")
            except Exception as e:
                print(f"Read Error: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_view()
