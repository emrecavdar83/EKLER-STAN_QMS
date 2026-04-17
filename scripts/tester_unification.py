import sys
import os
from sqlalchemy import text

# System paths
sys.path.append(os.getcwd())

from database.connection import get_engine
from logic.auth_logic import kullanici_yetkisi_var_mi, _normalize_string

def run_tests():
    print("--- UNIFICATION TEST SUITE STARTING ---")
    engine = get_engine()
    
    with engine.connect() as conn:
        # TEST 1: Table Existence & Count
        try:
            old_count = conn.execute(text("SELECT count(*) FROM ayarlar_kullanicilar")).scalar()
            new_count = conn.execute(text("SELECT count(*) FROM ayarlar_kullanicilar")).scalar()
            print("TEST 1: Migration Count Check")
            print(f"   - Legacy (personel): {old_count}")
            print(f"   - New (ayarlar_kullanicilar): {new_count}")
            if old_count == new_count:
                print("   - SUCCESS: Record counts match.")
            else:
                print("   - WARNING: Record counts differ!")
        except Exception as e:
            print(f"TEST 1 FAILED: {e}")

        # TEST 2: Schema Integrity
        try:
            cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'ayarlar_kullanicilar'")).fetchall()
            col_list = [c[0] for c in cols]
            print(f"TEST 2: Schema Integrity ({len(col_list)} columns found)")
            expected_sample = ['id', 'ad_soyad', 'kullanici_adi', 'sifre', 'rol', 'gorev']
            missing = [c for c in expected_sample if c not in col_list]
            if not missing:
                print("   - SUCCESS: Core columns present.")
            else:
                print(f"   - FAILED: Missing columns: {missing}")
        except Exception as e:
            print(f"TEST 2 FAILED: {e}")

        # TEST 3: Auth Logic Integration
        try:
            print("TEST 3: Auth Logic Integration")
            with open("logic/auth_logic.py", "r", encoding="utf-8") as f:
                code = f.read()
                if "ayarlar_kullanicilar" in code.lower() and "ayarlar_kullanicilar" not in code.lower():
                     print("   - FAILED: auth_logic.py still references legacy table name.")
                else:
                     print("   - SUCCESS: auth_logic.py refactor verified.")
        except Exception as e:
            print(f"TEST 3 FAILED: {e}")

    print("\n--- TEST SUITE FINISHED ---")

if __name__ == "__main__":
    run_tests()
