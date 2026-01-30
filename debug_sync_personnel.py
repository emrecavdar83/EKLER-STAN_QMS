import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

SECRETS_PATH = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
secrets = toml.load(SECRETS_PATH)
if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
    LIVE_DB_URL = secrets["streamlit"]["DB_URL"]
else:
    LIVE_DB_URL = secrets["DB_URL"]
if LIVE_DB_URL.startswith('"') and LIVE_DB_URL.endswith('"'):
    LIVE_DB_URL = LIVE_DB_URL[1:-1]

LOCAL_DB_URL = "sqlite:///ekleristan_local.db"
local_engine = create_engine(LOCAL_DB_URL)
live_engine = create_engine(LIVE_DB_URL)

table = "personel"
print(f"Syncing {table}...")

try:
    df_local = pd.read_sql(f"SELECT * FROM {table}", local_engine)
    print(f"Read {len(df_local)} records from Local.")

    # 1. Clean invalid yonetici_ids (pointing to non-existent IDs)
    valid_ids = set(df_local['id'].dropna().unique())
    
    # Store original yonetici_ids for later update
    # Ensure yonetici_id is float/numeric for comparison, handle NaNs
    df_local['yonetici_id'] = pd.to_numeric(df_local['yonetici_id'], errors='coerce')
    
    # Identify orphans
    orphans = df_local[
        (df_local['yonetici_id'].notna()) & 
        (~df_local['yonetici_id'].isin(valid_ids))
    ]
    if not orphans.empty:
        print(f"WARNING: Found {len(orphans)} records with invalid yonetici_id (orphans). Setting their manager to NULL.")
        print(f"Orphan IDs: {orphans['yonetici_id'].unique()}")
        # Fix orphans in the logical dataframe
        df_local.loc[orphans.index, 'yonetici_id'] = None

    # 1b. Clean invalid departman_ids (pointing to non-existent departments in LIVE DB)
    # We must fetch valid departments from Live DB first
    with live_engine.connect() as conn:
        valid_depts = set(pd.read_sql("SELECT id FROM ayarlar_bolumler", conn)['id'].unique())
    
    print(f"Valid Department IDs in Live DB: {sorted(list(valid_depts))}")
    
    invalid_dept_rows = df_local[
        (df_local['departman_id'].notna()) & 
        (~df_local['departman_id'].isin(valid_depts))
    ]
    
    if not invalid_dept_rows.empty:
        print(f"WARNING: Found {len(invalid_dept_rows)} records with invalid departman_id. Setting their department to NULL.")
        print(f"Invalid Department IDs: {invalid_dept_rows['departman_id'].unique()}")
        df_local.loc[invalid_dept_rows.index, 'departman_id'] = None

    # Prepare for 2-step insert
    # Step 1: Insert with yonetici_id = NULL to avoid FK violations
    df_insert = df_local.copy()
    original_managers = df_insert['yonetici_id'].copy() # Keep a copy of valid manager connections
    df_insert['yonetici_id'] = None # Nullify for first pass

    with live_engine.begin() as conn:
        print("Attempting delete...")
        conn.execute(text(f"DELETE FROM {table}"))
        print("Delete successful.")
        
        print("Attempting insert (Phase 1: No Managers)...")
        df_insert.to_sql(table, conn, if_exists='append', index=False)
        print("Insert Phase 1 successful.")
        
        # Step 2: Restore yonetici_id
        print("Attempting link update (Phase 2: Linking Managers)...")
        
        # Only update records that actually have a manager
        updates = []
        for index, row in df_local.iterrows():
            if pd.notna(row['yonetici_id']):
                updates.append({
                    'p_id': row['id'], 
                    'm_id': row['yonetici_id']
                })
        
        if updates:
            # Batch update might be slow record-by-record, but safe. 
            # Ideally use a temp table or bind params, but for <200 records loop is fine or executemany.
            stmt = text(f"UPDATE {table} SET yonetici_id = :m_id WHERE id = :p_id")
            conn.execute(stmt, updates)
            print(f"Linked {len(updates)} managers.")
        else:
            print("No managers to link.")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"ERROR: {e}")
