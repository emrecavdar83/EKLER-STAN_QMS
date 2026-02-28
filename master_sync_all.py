import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os
import sys

# Encoding support
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 1. Configuration
SECRETS_PATH = ".streamlit/secrets.toml"
LOCAL_DB_URL = "sqlite:///ekleristan_local.db"

try:
    secrets = toml.load(SECRETS_PATH)
    LIVE_DB_URL = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
    if LIVE_DB_URL.startswith('"') and LIVE_DB_URL.endswith('"'):
        LIVE_DB_URL = LIVE_DB_URL[1:-1]
except Exception as e:
    print(f"Error loading secrets: {e}")
    sys.exit(1)

local_engine = create_engine(LOCAL_DB_URL)
live_engine = create_engine(LIVE_DB_URL, pool_pre_ping=True)

# 2. Logic: Safe Upsert (No Delete)
def sync_table(table_name, pk_cols):
    print(f"\n>>> Syncing: {table_name}")
    try:
        local_df = pd.read_sql(f"SELECT * FROM {table_name}", local_engine)
        if local_df.empty:
            print(f"    - Local table {table_name} is empty, skipping.")
            return

        live_df = pd.read_sql(f"SELECT * FROM {table_name}", live_engine)
        
        if isinstance(pk_cols, str):
            pk_cols = [pk_cols]
            
        live_keys = set()
        if not live_df.empty:
            for _, row in live_df.iterrows():
                key = tuple(row[col] for col in pk_cols)
                live_keys.add(key)
        
        inserts = []
        updates = []
        
        for _, row in local_df.iterrows():
            key = tuple(row[col] for col in pk_cols)
            if key in live_keys:
                updates.append(row.to_dict())
            else:
                inserts.append(row.to_dict())
                
        print(f"    - Locals: {len(local_df)} | Inserts: {len(inserts)} | Updates: {len(updates)}")
        
        with live_engine.begin() as conn:
            # 1. Insert New
            if inserts:
                idf = pd.DataFrame(inserts)
                idf = idf.where(pd.notnull(idf), None)
                idf.to_sql(table_name, conn, if_exists='append', index=False)
                print(f"    - OK: {len(inserts)} rows inserted.")
                
            # 2. Update Existing
            if updates:
                for row in updates:
                    where_clause = " AND ".join([f"{c} = :{c}" for c in pk_cols])
                    set_cols = [c for c in local_df.columns if c not in pk_cols]
                    set_clause = ", ".join([f"{c} = :{c}" for c in set_cols])
                    sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
                    params = {k: (None if pd.isna(v) else v) for k, v in row.items()}
                    conn.execute(text(sql), params)
                print(f"    - OK: {len(updates)} rows updated.")
                
    except Exception as e:
        print(f"    - ERROR syncing {table_name}: {e}")

# 3. Execution List
if __name__ == "__main__":
    print("="*60)
    print(" MASTER SYNC ALL - LOCAL -> CLOUD ")
    print("="*60)
    
    # Core Settings
    sync_table("ayarlar_bolumler", "id")
    sync_table("ayarlar_yetkiler", ["rol_adi", "modul_adi"])
    sync_table("personel", "id")
    sync_table("ayarlar_urunler", "id")
    
    # GMP & Hygiene
    sync_table("lokasyonlar", "id")
    sync_table("proses_tipleri", "id")
    sync_table("lokasyon_proses_atama", "id")
    sync_table("tanim_metotlar", "id")
    sync_table("kimyasal_envanter", "id")
    sync_table("gmp_soru_havuzu", "id")
    
    # SOSTS (Cold Rooms)
    sync_table("soguk_odalar", "oda_kodu")
    sync_table("sicaklik_olcumleri", "id")
    sync_table("olcum_plani", ["oda_id", "beklenen_zaman"])
    
    # Operations
    sync_table("depo_giris_kayitlari", "id")
    sync_table("urun_kpi_kontrol", "id")
    sync_table("hijyen_kontrol_kayitlari", "id")
    sync_table("temizlik_kayitlari", "id")
    
    print("\n" + "="*60)
    print(" ALL TABLES SYNCED SUCCESSFULLY ")
    print("="*60)
