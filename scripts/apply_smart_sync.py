
import json
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os
import sys

# --- 1. CONFIG & CONNECTIONS ---
print("--- STARTED: SMART PERSONNEL APPLICATION (HARD DELETE MODE) ---")

# LOCAL
LOCAL_DB_URL = 'sqlite:///ekleristan_local.db'
local_engine = create_engine(LOCAL_DB_URL)

# LIVE
LIVE_DB_URL = None
try:
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
            LIVE_DB_URL = secrets["streamlit"]["DB_URL"]
        elif "DB_URL" in secrets:
            LIVE_DB_URL = secrets["DB_URL"]
        
        if LIVE_DB_URL and LIVE_DB_URL.startswith('"') and LIVE_DB_URL.endswith('"'):
            LIVE_DB_URL = LIVE_DB_URL[1:-1]
except Exception as e:
    print(f"Error loading secrets: {e}")

live_engine = None
if LIVE_DB_URL:
    try:
        live_engine = create_engine(LIVE_DB_URL)
        print("Connected to LIVE DB.")
    except Exception as e:
        print(f"Failed to connect to LIVE DB: {e}")
else:
    print("LIVE DB URL not found. Skipping Live DB updates.")

# --- 2. LOAD PAYLOAD ---
try:
    with open('sync_payload.json', 'r', encoding='utf-8') as f:
        payload = json.load(f)
    print("Payload loaded.")
except FileNotFoundError:
    print("Error: sync_payload.json not found. Run generate_target_state.py first.")
    sys.exit(1)

target_list = set(payload['target_list'])
renames = payload['renames'] # old -> new

# --- 3. EXECUTION FUNCTION ---
def apply_changes(engine, env_name):
    if engine is None: return

    print(f"\n[{env_name}] Applying changes...")
    
    with engine.begin() as conn:
        # A. RENAMES (Must be first to preserve IDs)
        # We need to be careful: if we rename "A" to "B", check if "B" already exists?
        # Assuming database constraints might handle uniqueness, but let's try.
        # User confirmed these are renames.
        print(f" - Processing {len(renames)} Renames...")
        for old, new in renames.items():
            # Check if old exists
            res = conn.execute(text("SELECT id FROM personel WHERE ad_soyad = :old"), {"old": old}).fetchone()
            if res:
                # Execute Rename
                # Note: If 'new' already exists, this might fail or merge depending on constraint.
                # Usually it shouldn't exist if it's a rename.
                try:
                    conn.execute(text("UPDATE personel SET ad_soyad = :new WHERE id = :id"), {"new": new, "id": res[0]})
                    print(f"   [RENAME] {old} -> {new}")
                except Exception as e:
                    print(f"   [ERROR RENAME] {old} -> {new}: {e}")
            else:
                 pass # Old name not found, maybe already renamed or deleted

        # B. FETCH CURRENT STATE
        # Get all current personnel
        current_db_df = pd.read_sql("SELECT id, ad_soyad FROM personel", conn)
        current_names = set(current_db_df['ad_soyad'].tolist()) if not current_db_df.empty else set()
        
        # C. INSERTS (In Target List but NOT in DB)
        to_add = target_list - current_names
        print(f" - Adding {len(to_add)} new records...")
        
        for name in to_add:
            print(f"   [ADD] {name}")
            conn.execute(text("INSERT INTO personel (ad_soyad, durum, pozisyon_seviye) VALUES (:n, 'AKTİF', 5)"), {"n": name})

        # D. HARD DELETES (In DB but NOT in Target List)
        # Caution: We must re-fetch state if we want to be super precise, but set difference is fine 
        # because we only added people who weren't there.
        # However, renames changed the DB state.
        
        # Let's handle Deletes by checking the *updated* DB state to be safe against double processing
        # Actually simplified logic:
        # DELETE FROM personel WHERE ad_soyad NOT IN target_list
        # But we must be careful about "Admin" users or system users?
        # User's list is the authority for the personnel list.
        # Let's exclude 'Admin' from deletion to prevent locking ourselves out.
        
        safe_list = list(target_list)
        # Add Admin to safe list if not present, just in case
        safe_list.append('Admin')
        safe_list.append('SİSTEM ADMİN')
        
        # We need to bind a list parameter. SQLAlchemy handles list binding with tuple.
        # However, lists can be large. 176 items is fine.
        
        if len(safe_list) > 0:
             # Construct parametrized query for safety
             # "DELETE FROM personel WHERE ad_soyad NOT IN :safe_list"
             # Postgres/SQLite support IN clause.
             
             # Get count first
             res_count = conn.execute(text("SELECT count(*) FROM personel WHERE ad_soyad NOT IN :safe_list"), {"safe_list": tuple(safe_list)}).fetchone()
             count_to_delete = res_count[0]
             
             print(f" - Deleting {count_to_delete} records (Ref: Hard Delete)...")
             
             if count_to_delete > 0:
                 conn.execute(text("DELETE FROM personel WHERE ad_soyad NOT IN :safe_list"), {"safe_list": tuple(safe_list)})
        
        # E. REACTIVATE (Just in case they exist but are Passive, though we insert as Active)
        # If they were already in DB (so not added in step C) but were Passive, we should set them Active.
        # UPDATE personel SET durum = 'AKTİF' WHERE ad_soyad IN target_list AND durum != 'AKTİF'
        
        conn.execute(text("UPDATE personel SET durum = 'AKTİF' WHERE ad_soyad IN :target_list AND (durum != 'AKTİF' OR durum IS NULL)"), {"target_list": tuple(target_list)})
        print(" - Ensured all target records are AKTİF.")

    print(f"[{env_name}] Completed.")

# --- 4. RUN ---
apply_changes(local_engine, "LOCAL")
apply_changes(live_engine, "LIVE")

print("\n--- DONE ---")
