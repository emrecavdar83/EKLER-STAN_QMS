import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

# 1. Config
SECRETS_PATH = ".streamlit/secrets.toml"
INPUT_FILE = 'personnel_update_20260131.txt'

# 2. Load Whitelist
def normalize_name(name):
    if not name: return ""
    n = name.strip().upper()
    n = n.replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
    n = n.replace(' ', '')
    return n

print(f"Reading {INPUT_FILE}...")
whitelist = set()
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('Sno'): continue
        parts = line.split('\t')
        if len(parts) >= 2:
            whitelist.add(normalize_name(parts[1]))

print(f"Whitelist loaded: {len(whitelist)} names.")

# 3. Connect to Live
print("Connecting to Live DB...")
secrets = toml.load(SECRETS_PATH)
url = secrets["streamlit"]["DB_URL"]
if url.startswith('"') and url.endswith('"'): url = url[1:-1]
engine = create_engine(url)

# 4. Find Ghosts
with engine.connect() as conn:
    print("Fetching Active Users from Live...")
    result = conn.execute(text("SELECT id, ad_soyad FROM personel WHERE durum = 'AKTİF' OR durum IS NULL"))
    active_users = result.fetchall()
    
    ghosts = []
    found_whitelist = 0
    
    for row in active_users:
        uid = row[0]
        name = row[1]
        norm = normalize_name(name)
        
        if norm in whitelist:
            found_whitelist += 1
        else:
            ghosts.append((uid, name))
            
    print(f"Total Active in Live: {len(active_users)}")
    print(f"Matched Whitelist: {found_whitelist}")
    print(f"Ghosts Found: {len(ghosts)}")
    
    if ghosts:
        print("\nDeactivating Ghosts:")
        for uid, name in ghosts:
            print(f" - Deactivating: {name} (ID: {uid})")
            
        ghost_ids = [g[0] for g in ghosts]
        # Batch Update
        # Using text() with bindparams for list is tricky in some drivers, looping is safer for small count
        # or stick to string formatting if reliable (risk of injection but these are ints)
        
        stmt = text("UPDATE personel SET durum = 'PASİF' WHERE id = :uid")
        for uid in ghost_ids:
            conn.execute(stmt, {"uid": uid})
            
        conn.commit()
        print(f"\nSuccessfully deactivated {len(ghosts)} records.")
    else:
        print("No ghosts found. Database is clean.")
    
    # Final Check
    final_count = conn.execute(text("SELECT count(*) FROM personel WHERE durum = 'AKTİF'")).scalar()
    print(f"Final Active Count: {final_count}")

