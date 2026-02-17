import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///ekleristan_local.db')
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='view' AND name='v_organizasyon_semasi'")).fetchone()
        if result:
            print("View Definition:")
            print(result[0])
        else:
            print("View v_organizasyon_semasi not found in sqlite_master")
            
        print("\n--- Fallback: Check if table exists ---")
        # Check if it is a table instead of view?
        result_tbl = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='v_organizasyon_semasi'")).fetchone()
        if result_tbl:
            print("It is a TABLE:")
            print(result_tbl[0])

except Exception as e:
    print(f"Error: {e}")
