
import sqlite3
from sqlalchemy import create_engine, text
import time
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from soguk_oda_utils import plan_uret, init_sosts_tables

def test_optimization():
    print("--- SOSTS OPTIMIZATION TEST ---")
    engine = create_engine('sqlite:///ekleristan_local.db')
    
    # 1. Init tables
    init_sosts_tables(engine)
    
    # 2. First run (should generate slots)
    print("Running plan_uret (First run)...")
    start = time.time()
    plan_uret(engine)
    end = time.time()
    first_duration = end - start
    print(f"First run duration: {first_duration:.4f}s")
    
    # 3. Second run (should be faster due to Smart Check skip)
    print("\nRunning plan_uret (Second run - Smart Check)...")
    start = time.time()
    plan_uret(engine)
    end = time.time()
    second_duration = end - start
    print(f"Second run duration: {second_duration:.4f}s")
    
    improvement = (first_duration - second_duration) / first_duration * 100
    print(f"\nImprovement: %{improvement:.2f}")
    
    if second_duration < first_duration or second_duration < 0.05:
        print("\n✅ Verification SUCCESS: Smart Check is working and skipping unnecessary work.")
    else:
        print("\n❌ Verification FAILED: Second run was not significantly faster.")

if __name__ == "__main__":
    test_optimization()
