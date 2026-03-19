import time
from sqlalchemy import create_engine, text
import pandas as pd

# Secrets from secrets.toml
DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def run_remote_diag():
    print(f"Connecting to {DB_URL.split('@')[1]}...")
    t0 = time.time()
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        t1 = time.time()
        print(f"DB Connection established in: {t1-t0:.3f} sn")
        
        # Test 1: Full table scan check
        print("\nChecking table sizes...")
        for t in ['map_vardiya', 'map_zaman_cizelgesi', 'map_fire_kaydi']:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"- {t}: {count} rows")
            
        # Test 2: Index analysis
        print("\nChecking indexes...")
        idx_sql = """
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename IN ('map_vardiya', 'map_zaman_cizelgesi', 'map_fire_kaydi')
        """
        idxs = pd.read_sql(idx_sql, conn)
        print(idxs)
        
        # Test 3: Common queries latency
        print("\nTesting common query latency...")
        # Simulate many queries to see the cumulative effect
        queries = [
            "SELECT * FROM map_vardiya WHERE durum='ACIK' ORDER BY makina_no ASC",
            "SELECT * FROM map_vardiya WHERE id=1 LIMIT 1", # Assuming ID 1 exists
            "SELECT id, baslangic_ts FROM map_zaman_cizelgesi WHERE vardiya_id=1 AND bitis_ts IS NULL",
            "SELECT * FROM map_zaman_cizelgesi WHERE vardiya_id=1 ORDER BY sira_no"
        ]
        
        total_q_time = 0
        for i, q in enumerate(queries):
            ts = time.time()
            try:
                conn.execute(text(q)).fetchall()
                te = time.time()
                diff = te - ts
                print(f"Query {i+1} took: {diff:.3f} sn")
                total_q_time += diff
            except:
                print(f"Query {i+1} failed (ID mismatch or table issue)")
        
        print(f"\nTotal latency for 4 queries: {total_q_time:.3f} sn")

if __name__ == "__main__":
    run_remote_diag()
