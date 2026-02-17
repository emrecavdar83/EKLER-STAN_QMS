
import sqlite3
import pandas as pd
import os

DB_PATH = 'ekleristan_local.db'

def rebuild_personnel():
    print("--- Rebuilding Local Personnel Table (Clean Start) ---")
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Fetch ALL active personnel
    query = "SELECT * FROM personel WHERE durum = 'AKTİF'"
    df_active = pd.read_sql(query, conn)
    print(f"Found {len(df_active)} active personnel.")

    # 2. Get name mapping for managers (to restore hierarchy)
    # We need to map old_id -> name, then later name -> new_id
    id_to_name = {row['id']: row['ad_soyad'] for _, row in df_active.iterrows()}
    
    # 3. Wipe and Reset Table
    cursor = conn.cursor()
    cursor.execute("DELETE FROM personel")
    # Reset SQLite internal sequence
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='personel'")
    conn.commit()
    print("Local personnel table wiped and sequence reset.")

    # 4. Re-insert active personnel
    # Sort them by original ID or Name to keep some order
    df_to_insert = df_active.copy()
    df_to_insert = df_to_insert.sort_values(by='id') # Keep original order preference
    
    # We'll drop the 'id' column so SQLite generates new ones from 1
    cols_to_keep = [c for c in df_to_insert.columns if c != 'id']
    
    # Store manager assignments by NAME for stage 2
    manager_assignments = []
    for _, row in df_to_insert.iterrows():
        if pd.notnull(row['yonetici_id']):
            mgr_name = id_to_name.get(row['yonetici_id'])
            if mgr_name:
                manager_assignments.append((row['ad_soyad'], mgr_name))

    # Insert back (ID will be auto-generated from 1)
    for _, row in df_to_insert[cols_to_keep].iterrows():
        # Handle yonetici_id separately (set to NULL initially)
        data = row.to_dict()
        data['yonetici_id'] = None
        
        placeholders = ", ".join(["?"] * len(data))
        columns = ", ".join(data.keys())
        sql = f"INSERT INTO personel ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
    
    conn.commit()
    print("Active personnel re-inserted with new IDs.")

    # 5. Restore Hierarchy (Name -> New ID Mapping)
    cursor.execute("SELECT id, ad_soyad FROM personel")
    new_id_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    updated_mgrs = 0
    for staff_name, mgr_name in manager_assignments:
        staff_id = new_id_map.get(staff_name)
        mgr_id = new_id_map.get(mgr_name)
        if staff_id and mgr_id:
            cursor.execute("UPDATE personel SET yonetici_id = ? WHERE id = ?", (mgr_id, staff_id))
            updated_mgrs += 1
            
    conn.commit()
    print(f"Restored {updated_mgrs} manager relationships using new IDs.")
    
    # Final count check
    cursor.execute("SELECT COUNT(*) FROM personel")
    total = cursor.fetchone()[0]
    print(f"Final local count: {total}")
    
    conn.close()
    print("--- Local Rebuild Complete ---")

if __name__ == "__main__":
    rebuild_personnel()
