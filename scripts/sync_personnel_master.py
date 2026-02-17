
import os
import sqlite3
import pandas as pd
import shutil
from datetime import datetime
import re

# Config
DATA_FILE = "personnel_update_20260131.txt"
DB_PATH = "ekleristan_local.db"
BACKUP_PATH = f"ekleristan_local_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_db():
    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, BACKUP_PATH)
        print(f"✅ Database backed up to: {BACKUP_PATH}")
    else:
        print("⚠️ Database not found!")

def normalize_name(name):
    """Normalize Turkish characters and case for comparison."""
    if not name: return ""
    name = name.replace("İ", "i").replace("I", "ı").lower().strip()
    return name

def parse_master_list(filepath):
    """Parses the tab-separated or fixed-width text file."""
    print(f"📂 Reading master list from: {filepath}")
    
    personnel = []
    
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Skip header (usually line 0)
    start_idx = 1 if "Sno" in lines[0] else 0
    
    for line in lines[start_idx:]:
        parts = line.strip().split("\t")
        # Fallback: if not tab separated, try double space
        if len(parts) < 2:
            parts = re.split(r'\s{2,}', line.strip())
            
        if len(parts) < 2: continue # Skip empty or invalid lines
        
        # Mapping based on: Sno | Adı Soyadı | Bölüm | VARDİYA | SERVİS DURAĞI | TEL
        # Note: Index might vary if parts are missing.
        # We assume strict order as per user copy-paste.
        
        # Handling potentially missing columns at the end (TEL might be empty)
        sno = parts[0]
        name = parts[1]
        dept = parts[2] if len(parts) > 2 else ""
        shift = parts[3] if len(parts) > 3 else "Gündüz Vardiyası"
        service = parts[4] if len(parts) > 4 else ""
        phone = parts[5] if len(parts) > 5 else ""
        
        # Clean phone
        phone = re.sub(r'\D', '', phone)
        if len(phone) > 10 and phone.startswith('90'): phone = phone[2:]
        if len(phone) == 10 and not phone.startswith('0'): phone = '0' + phone

        personnel.append({
            "ad_soyad": name.strip(),
            "bolum_text": dept.strip(),
            "vardiya": shift.strip(),
            "servis": service.strip(),
            "tel": phone
        })
        
    print(f"✅ Parsed {len(personnel)} records from text file.")
    return personnel

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def fetch_departments(conn):
    """Returns a map of {Normalized Name: ID} and {Original Name: ID}"""
    df = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", conn)
    dept_map = {}
    
    for _, row in df.iterrows():
        d_id = row['id']
        name = row['bolum_adi']
        dept_map[name] = d_id
        dept_map[normalize_name(name)] = d_id
        
        # Extra aliases
        if "PATASU" in normalize_name(name): dept_map["pataşu"] = d_id
        if "PROFIT" in normalize_name(name): dept_map["profiterol"] = d_id
        
    return dept_map

def fetch_managers(conn):
    """Returns a map of {DeptID: ManagerID}."""
    # Logic: Find 'Bölüm Sorumlusu', 'Vardiya Amiri' or 'Admin' in that department
    # Priority: Admin > Sorumlu > Amir
    
    sql = """
    SELECT id, departman_id, rol FROM personel 
    WHERE rol IN ('Admin', 'Bölüm Sorumlusu', 'Vardiya Amiri', 'Genel Müdür')
    AND departman_id IS NOT NULL AND departman_id != 0
    ORDER BY CASE rol 
        WHEN 'Genel Müdür' THEN 10 
        WHEN 'Bölüm Sorumlusu' THEN 5 
        WHEN 'Vardiya Amiri' THEN 2 
        WHEN 'Admin' THEN 1 
        ELSE 0 END DESC
    """
    df = pd.read_sql(sql, conn)
    
    manager_map = {}
    for _, row in df.iterrows():
        d_id = row['departman_id']
        if d_id not in manager_map: # Highest priority comes first due to sort
            manager_map[d_id] = row['id']
            
    return manager_map

def sync_personnel():
    backup_db()
    
    master_list = parse_master_list(DATA_FILE)
    if not master_list:
        print("❌ No data found in master list. Aborting.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 0. Pre-load Maps
    dept_map = fetch_departments(conn)
    manager_map = fetch_managers(conn)
    
    # 1. Identify Existing Personnel
    print("🔍 Analyzing existing database...")
    existing_df = pd.read_sql("SELECT id, ad_soyad FROM personel", conn)
    
    # Create normalized map: {norm_name: [id1, id2]}
    db_personnel = {}
    for _, row in existing_df.iterrows():
        norm = normalize_name(row['ad_soyad'])
        if norm not in db_personnel: db_personnel[norm] = []
        db_personnel[norm].append(row['id'])
        
    # Master list names set
    master_names_norm = set(normalize_name(p['ad_soyad']) for p in master_list)
    
    # 2. DELETE Logic (Not in Master List)
    print("🗑️ Checking for deletions...")
    to_delete_ids = []
    ids_kept_count = 0
    
    for norm_name, ids in db_personnel.items():
        if norm_name not in master_names_norm:
            # Delete ALL IDs associated with this name
            to_delete_ids.extend(ids)
        else:
            # Name exists in master list.
            # Convert duplicates to delete list (Keep the one with lowest ID - usually oldest)
            if len(ids) > 1:
                ids.sort()
                # Keep first (0), delete rest
                to_delete_ids.extend(ids[1:])
                # Log that we kept only ids[0]
                db_personnel[norm_name] = [ids[0]] # Update map to reflect single ID
            
    if to_delete_ids:
        print(f"⚠️ Deleting {len(to_delete_ids)} records (Missing in master list or duplicates)...")
        # Chunked delete
        chunk_size = 500
        for i in range(0, len(to_delete_ids), chunk_size):
            chunk = to_delete_ids[i:i+chunk_size]
            placeholders = ','.join(['?']*len(chunk))
            cursor.execute(f"DELETE FROM personel WHERE id IN ({placeholders})", chunk)
        conn.commit()
    else:
        print("✓ No deletions needed.")
        
    # 3. UPDATE / INSERT Logic
    print("💾 Syncing Master List...")
    updated_count = 0
    inserted_count = 0
    
    for p in master_list:
        norm_name = normalize_name(p['ad_soyad'])
        original_name = p['ad_soyad']
        
        # Resolve Dept ID
        dept_text = p['bolum_text']
        dept_id = dept_map.get(normalize_name(dept_text)) or dept_map.get(dept_text)
        
        if not dept_id and dept_text:
             # Try partial match if not found?
             # For now, default to None or 0
             dept_id = 0
             
        # Resolve Manager ID
        manager_id = manager_map.get(dept_id) if dept_id else None
        
        # Check if exists (using our cleaned db_personnel map)
        existing_ids = db_personnel.get(norm_name)
        
        if existing_ids:
            # UPDATE
            pid = existing_ids[0] # We ensured single ID above
            
            # Fields to update: bolum (text), departman_id, yonetici_id, vardiya, servis, tel, durum='AKTİF'
            cursor.execute("""
                UPDATE personel 
                SET bolum = ?, departman_id = ?, yonetici_id = ?, 
                    vardiya = ?, servis_duragi = ?, telefon_no = ?, 
                    durum = 'AKTİF'
                WHERE id = ?
            """, (
                dept_text, dept_id, manager_id, 
                p['vardiya'], p['servis'], p['tel'], 
                pid
            ))
            updated_count += 1
        else:
            # INSERT
            cursor.execute("""
                INSERT INTO personel 
                (ad_soyad, bolum, departman_id, yonetici_id, vardiya, servis_duragi, telefon_no, durum, pozisyon_seviye)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'AKTİF', 5)
            """, (
                original_name, dept_text, dept_id, manager_id, 
                p['vardiya'], p['servis'], p['tel']
            ))
            inserted_count += 1
            
    conn.commit()
    conn.close()
    
    print("-" * 50)
    print("🎉 SYNCHRONIZATION COMPLETE")
    print(f"❌ Deleted: {len(to_delete_ids)}")
    print(f"✏️ Updated: {updated_count}")
    print(f"➕ Inserted: {inserted_count}")
    
if __name__ == "__main__":
    sync_personnel()
