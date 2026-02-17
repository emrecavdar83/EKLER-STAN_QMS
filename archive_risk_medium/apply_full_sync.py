import sqlite3
import re
import sys

DB_PATH = 'ekleristan_local.db'
INPUT_FILE = 'personnel_update_20260131.txt'

def normalize_name(name):
    """Normalize Turkish characters and remove spaces for comparison."""
    if not name: return ""
    # Map Turkish chars to English approximations for loose matching, or keep strict if preferred.
    # Given the previous context, strict but case-insensitive + ignore space is best.
    # But let's handle the specific corrections mentioned in the report (e.g. I/İ confusion).
    n = name.strip().upper()
    n = n.replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
    n = n.replace(' ', '')
    return n

def parse_file(filepath):
    """Parse the tab-separated file."""
    people = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('Sno'): continue
            
            # Split by tab
            parts = [p.strip() for p in line.split('\t') if p.strip()]
            
            # Handle cases where tabs might be missing or different format
            # The file viewing showed: Sno, Name, Dept, Shift, Loc, Tel
            # 1 ABDALRAOUF... PROFITEROL ...
            
            if len(parts) < 3:
                # Try splitting by multiple spaces if tabs failed
                parts = [p.strip() for p in re.split(r'\s{2,}', line) if p.strip()]
            
            if len(parts) < 2:
                print(f"Skipping malformed line: {line}")
                continue

            # Mapping based on observed structure:
            # Index 0: Sno (ignore)
            # Index 1: Name
            # Index 2: Dept/Role
            # Index 3: Shift
            # Index 4: Service Location
            # Index 5: Phone (Optional)
            
            try:
                name = parts[1]
                role = parts[2] if len(parts) > 2 else "Personel"
                shift = parts[3] if len(parts) > 3 else ""
                location = parts[4] if len(parts) > 4 else ""
                phone = parts[5] if len(parts) > 5 else ""
                
                people.append({
                    "name": name,
                    "role": role,
                    "shift": shift,
                    "location": location,
                    "phone": phone,
                    "norm": normalize_name(name)
                })
            except IndexError:
                print(f"Error parsing line: {line}")
                
    return people

def sync_db():
    print(f"Reading {INPUT_FILE}...")
    file_people = parse_file(INPUT_FILE)
    print(f"Parsed {len(file_people)} records from file.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure columns exist
    cursor.execute("PRAGMA table_info(personnel)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'servis_duragi' not in columns:
        cursor.execute("ALTER TABLE personnel ADD COLUMN servis_duragi TEXT")
    if 'telefon_no' not in columns:
        cursor.execute("ALTER TABLE personnel ADD COLUMN telefon_no TEXT")
    
    # Fetch existing users
    cursor.execute("SELECT id, ad_soyad FROM personnel")
    db_users = {} # norm_name -> id
    for row in cursor.fetchall():
        db_users[normalize_name(row[1])] = row[0]
        
    print(f"Found {len(db_users)} existing records in DB.")
    
    stats = {"added": 0, "updated": 0, "deactivated": 0}
    
    # Track processed IDs to know who is left (to deactivate)
    processed_ids = set()

    for person in file_people:
        norm = person['norm']
        name = person['name']
        role = person['role']
        shift = person['shift']
        location = person['location']
        phone = person['phone']
        
        if norm in db_users:
            # Update
            pid = db_users[norm]
            cursor.execute("""
                UPDATE personnel 
                SET ad_soyad = ?, bolum = ?, gorev = ?, vardiya = ?, servis_duragi = ?, telefon_no = ?, durum = 'AKTİF'
                WHERE id = ?
            """, (name, role, role, shift, location, phone, pid))
            stats['updated'] += 1
            processed_ids.add(pid)
        else:
            # Insert
            cursor.execute("""
                INSERT INTO personnel (ad_soyad, bolum, gorev, vardiya, servis_duragi, telefon_no, durum)
                VALUES (?, ?, ?, ?, ?, ?, 'AKTİF')
            """, (name, role, role, shift, location, phone))
            stats['added'] += 1
            
    # Deactivate others
    all_ids = set(db_users.values())
    msg_ids = all_ids - processed_ids
    
    if msg_ids:
        placeholders = ','.join('?' for _ in msg_ids)
        cursor.execute(f"UPDATE personnel SET durum = 'PASİF' WHERE id IN ({placeholders})", list(msg_ids))
        stats['deactivated'] = len(msg_ids)

    conn.commit()
    conn.close()
    
    print("\nSync Complete:")
    print(f" - Added: {stats['added']}")
    print(f" - Updated: {stats['updated']}")
    print(f" - Deactivated: {stats['deactivated']}")
    print(f" - Total Active in File: {len(file_people)}")

if __name__ == "__main__":
    sync_db()
