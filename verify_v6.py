
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import numpy as np

# Add project path
sys.path.append('c:/Projeler/S_program/EKLERİSTAN_QMS')
import soguk_oda_utils

def verify_v6_logic():
    try:
        db_path = 'c:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db'
        engine = create_engine(f'sqlite:///{db_path}')
        
        print("--- Step 1: Initialize/Update Tables ---")
        soguk_oda_utils.init_sosts_tables(engine)
        
        print("--- Step 2: Configure Per-Room Rules (Madde 1) ---")
        
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM soguk_oda_planlama_kurallari"))
            room_ids = conn.execute(text("SELECT id FROM soguk_odalar WHERE aktif = 1 LIMIT 2")).fetchall()
            if len(room_ids) < 2:
                print("Error: Need at least 2 active rooms for test.")
                return
            
            rid1 = room_ids[0][0]
            rid2 = room_ids[1][0]
            
            # Use rules that will definitely generate slots regardless of current time (0-24 coverage)
            conn.execute(text("""
                INSERT INTO soguk_oda_planlama_kurallari (oda_id, kural_adi, baslangic_saati, bitis_saati, siklik, kural_durumu)
                VALUES (:rid, 'Vardiya 1', 0, 8, 2, 'Ölçüm'),
                       (:rid, 'Vardiya 2', 8, 16, 2, 'Ölçüm'),
                       (:rid, 'Vardiya 3', 16, 24, 2, 'Ölçüm')
            """), {"rid": rid1})
            
            conn.execute(text("""
                INSERT INTO soguk_oda_planlama_kurallari (oda_id, kural_adi, baslangic_saati, bitis_saati, siklik, kural_durumu)
                VALUES (:rid, 'Bakım Peryodu', 0, 24, 4, 'Bakım')
            """), {"rid": rid2})
            
            conn.execute(text("DELETE FROM olcum_plani WHERE oda_id IN (:r1, :r2)"), {"r1": rid1, "r2": rid2})
        
        print("--- Step 3: Run Plan Generation ---")
        # Increase gun_sayisi to ensure we jump over "now"
        soguk_oda_utils.plan_uret(engine, gun_sayisi=2)
        
        print("--- Step 4: Verify Results ---")
        query = """
            SELECT o.oda_adi, p.beklenen_zaman, p.durum
            FROM olcum_plani p
            JOIN soguk_odalar o ON p.oda_id = o.id
            WHERE p.oda_id IN (:r1, :r2)
            ORDER BY o.oda_adi, p.beklenen_zaman
        """
        results = pd.read_sql(text(query), engine, params={"r1": rid1, "r2": rid2})
        print(f"\nGenerated Slots for test rooms ({len(results)} total):")
        print(results.head(10))
        
        if len(results) == 0:
            print("FAILED: No slots generated.")
            return

        r1_results = results[results['oda_id'] == rid1]
        r2_results = results[results['oda_id'] == rid2]
        
        print(f"\nRoom 1 Generated {len(r1_results)} slots.")
        print(f"Room 2 Generated {len(r2_results)} slots.")
        
        success = True
        if 'DURDURULDU' not in r2_results['durum'].unique():
            print("FAILED: Room 2 Maintenance status 'DURDURULDU' not found.")
            success = False
            
        if len(r1_results) < 5:
            print("FAILED: Room 1 should have generated more than 5 slots for 2 days.")
            success = False
            
        if success:
            print("\n✅ SUCCESS: Ultra-Dynamic logic verified!")
        
    except Exception as e:
        print(f"Verification Error: {e}")

if __name__ == "__main__":
    verify_v6_logic()
