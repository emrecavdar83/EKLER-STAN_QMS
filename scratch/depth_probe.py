import sys
import os
from sqlalchemy import text

# Add workspace to path
sys.path.append(os.getcwd())

from database.connection import get_engine

def probe_database():
    print("--- DATABASE DEPTH PROBE ---")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # 1. Get all tables
            res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
            tables = [r[0] for r in res]
            print(f"Current Tables: {tables}")
            
            # 2. Check if ayarlar_kullanicilar exists and has data
            if 'ayarlar_kullanicilar' in tables:
                cnt = conn.execute(text("SELECT count(*) FROM ayarlar_kullanicilar")).scalar()
                print(f"ayarlar_kullanicilar row count: {cnt}")
            else:
                print("ayarlar_kullanicilar table is MISSING.")
                
            # 3. Check if personel still exists
            if 'personel' in tables:
                cnt = conn.execute(text("SELECT count(*) FROM personel")).scalar()
                print(f"personel row count: {cnt}")
                
            # 4. Check for constraints
            print("\nChecking foreign keys pointing to personel vs ayarlar_kullanicilar...")
            sql = text("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                  AND ccu.table_name IN ('personel', 'ayarlar_kullanicilar');
            """)
            fks = conn.execute(sql).fetchall()
            for fk in fks:
                print(f"FK: {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
                
    except Exception as e:
        print(f"PROBE ERROR: {e}")

if __name__ == "__main__":
    probe_database()
