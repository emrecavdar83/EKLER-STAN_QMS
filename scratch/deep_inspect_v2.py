import sys
import os
from sqlalchemy import text

# Add workspace to path
sys.path.append(os.getcwd())

from database.connection import get_engine

def deep_inspect():
    print("--- EKLERİSTAN QMS: DEEP INSPECTION ---")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # 1. Get exact columns of 'personel'
            print("\n[PERSONEL SCHEMA]")
            query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'personel'
                ORDER BY ordinal_position;
            """)
            res = conn.execute(query).fetchall()
            cols_list = []
            for r in res:
                print(f"COL: {r[0]} ({r[1]})")
                cols_list.append(str(r[0]))
            
            # Save to file for model to read
            with open("scratch/personel_columns_final.txt", "w") as f:
                f.write("\n".join(cols_list))
                
            # 2. Check if 'ayarlar_kullanicilar' exists
            print("\n[AYARLAR_KULLANICILAR STATUS]")
            check = conn.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_name = 'ayarlar_kullanicilar'")).scalar()
            if check > 0:
                print("Table EXISTS.")
                cols = conn.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_name = 'ayarlar_kullanicilar'")).scalar()
                rows = conn.execute(text("SELECT count(*) FROM ayarlar_kullanicilar")).scalar()
                print(f"Columns: {cols}, Rows: {rows}")
            else:
                print("Table MISSING.")

    except Exception as e:
        print(f"DEBUG ERROR: {e}")

if __name__ == "__main__":
    deep_inspect()
