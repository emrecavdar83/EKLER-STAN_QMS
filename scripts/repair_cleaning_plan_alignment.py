import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

def repair_alignment():
    with engine.connect() as conn:
        # 1. Verileri çek
        plan_df = pd.read_sql("SELECT id, kat, kat_bolum, yer_ekipman FROM ayarlar_temizlik_plani", conn)
        lokasyonlar = pd.read_sql("SELECT id, ad, tip FROM lokasyonlar", conn)
        ekipmanlar = pd.read_sql("SELECT id, ekipman_adi FROM tanim_ekipmanlar", conn)
        
        # Mapping tabloları
        kat_map = {row['ad']: row['id'] for _, row in lokasyonlar[lokasyonlar['tip']=='Kat'].iterrows()}
        bolum_map = {row['ad']: row['id'] for _, row in lokasyonlar[lokasyonlar['tip']=='Bölüm'].iterrows()}
        ekip_map = {row['ekipman_adi']: row['id'] for _, row in ekipmanlar.iterrows()}
        
        mismatches = []
        updates = []
        
        for _, row in plan_df.iterrows():
            p_id = row['id']
            k_name = str(row['kat']).strip()
            b_name = str(row['kat_bolum']).strip()
            e_name = str(row['yer_ekipman']).strip()
            
            k_id = kat_map.get(k_name)
            b_id = bolum_map.get(b_name)
            e_id = ekip_map.get(e_name)
            
            if not k_id or not b_id or not e_id:
                mismatches.append({
                    "plan_id": p_id,
                    "kat": k_name if not k_id else "OK",
                    "bolum": b_name if not b_id else "OK",
                    "ekipman": e_name if not e_id else "OK"
                })
            
            # Update listesi (Mevcut olanları eşle)
            updates.append({
                "rid": p_id,
                "kid": k_id if k_id else None,
                "bid": b_id if b_id else None,
                "eid": e_id if e_id else None
            })
            
        # 2. Update Uygula
        with engine.begin() as trans_conn:
            for up in updates:
                trans_conn.execute(text("""
                    UPDATE ayarlar_temizlik_plani 
                    SET kat_id = :kid, bolum_id = :bid, ekipman_id = :eid, is_migrated = TRUE 
                    WHERE id = :rid
                """), up)
        
        print(f"--- REPAIR SUMMARY ---")
        print(f"Total Rows: {len(plan_df)}")
        print(f"Update applied to ALL rows (mapped where possible).")
        
        if mismatches:
            print(f"\n--- MISMATCHES (Requires manual addition to master tables) ---")
            m_df = pd.DataFrame(mismatches)
            print(m_df)
            m_df.to_csv("cleaning_mismatches_report.csv", index=False)
            print("Report saved to cleaning_mismatches_report.csv")
        else:
            print("\nAll records matched perfectly!")

if __name__ == "__main__":
    repair_alignment()
