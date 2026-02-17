import sqlite3
import re

DB_PATH = 'ekleristan_local.db'
INPUT_FILE = 'personnel_update_20260131.txt'

def normalize_string(s):
    if not s: return None
    return s.strip()

def parse_line(line):
    # try tab split first
    parts = [p.strip() for p in line.split('\t') if p.strip()]
    if len(parts) >= 4:
        # It was tab separated
        phone = parts[4] if len(parts) >= 5 else None
        return {
            "name": parts[0],
            "role": parts[1],
            "shift": parts[2],
            "location": parts[3],
            "phone": phone
        }

    # Fallback to Regex Anchor
    # Pattern: NAME_AND_ROLE   SHIFT   LOCATION_AND_PHONE
    # Shift is distinct: \d{2}:\d{2}\s*/\s*\d{2}:\d{2}
    
    match = re.search(r'(.+?)\s+(\d{2}:\d{2}\s*/\s*\d{2}:\d{2})\s+(.+)', line)
    if not match:
        return None
        
    before_shift = match.group(1).strip()
    shift = match.group(2).strip()
    after_shift = match.group(3).strip()
    
    # Process After Shift (Location + Optional Phone)
    phone = None
    location = after_shift
    
    # Check for phone at the end
    phone_match = re.search(r'\s(\d{9,11})$', after_shift)
    if phone_match:
        phone = phone_match.group(1)
        location = after_shift[:phone_match.start()].strip()
        
    # Process Before Shift (Name + Role)
    # This is harder without a fixed list of roles.
    # But usually Role is the last word or two?
    # Roles in example: KREMA, GENEL TEMİZLİK, FIRIN, BULAŞIKHANE
    
    roles = ["GENEL TEMİZLİK", "KREMA", "FIRIN", "BULAŞIKHANE", "DEPO", "SEVKİYAT", "PANDİSPANYA", "SOS", "BOMBA", "RULO PASTA", "HALKA TATLI", "ET İŞLEME", "BAKIM", "İ.K.", "SNOWLAND", "KALİTE", "PLANLAMA", "YÖNETİM"]
    
    found_role = None
    name = before_shift
    
    for r in roles:
        if before_shift.endswith(r):
            # verify it's a separate word check?
            found_role = r
            name = before_shift[:-len(r)].strip()
            break
            
    if not found_role:
        # Fallback: assume last word is role if single word?
        pass 
        # For now, if role not found in list, might be tricky.
        # But let's trust the user provided standard roles.
        # If "AHMAD KALLAJO KREMA", ends with KREMA.
        
    return {
        "name": name,
        "role": found_role if found_role else "Personel", # Default if parse fails
        "shift": shift,
        "location": location,
        "phone": phone
    }

def normalize_name(name):
    if not name: return ""
    return name.upper().replace('İ','I').replace('Ğ','G').replace('Ü','U').replace('Ş','S').replace('Ö','O').replace('Ç','C').replace(' ','')

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Ensure columns exist
    print("Checking schema...")
    cursor.execute("PRAGMA table_info(personnel)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'servis_duragi' not in columns:
        print("Adding 'servis_duragi' column...")
        cursor.execute("ALTER TABLE personnel ADD COLUMN servis_duragi TEXT")
        
    if 'telefon_no' not in columns:
        print("Adding 'telefon_no' column...")
        cursor.execute("ALTER TABLE personnel ADD COLUMN telefon_no TEXT")
    
    conn.commit()
    
    # Pre-fetch all names for normalized comparison
    cursor.execute("SELECT id, ad_soyad FROM personnel")
    existing_users = []
    for row in cursor.fetchall():
        existing_users.append({'id': row[0], 'name': row[1], 'norm': normalize_name(row[1])})

    # 2. Process File
    print("Processing file...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if "BURADAKİ LİSTEDEKİ" in line: continue
            if not line.strip(): continue
            
            data = parse_line(line)
            if not data:
                print(f"Skipping unparseable line: {line.strip()}")
                continue
                
            name = data['name']
            role = data['role']
            shift = data['shift']
            location = data['location']
            phone = data['phone']
            
            norm_name = normalize_name(name)
            
            # Find match
            match = next((u for u in existing_users if u['norm'] == norm_name), None)
            
            if match:
                # Update
                pid = match['id']
                print(f"Updating {name} (ID: {pid})...")
                cursor.execute("""
                    UPDATE personnel 
                    SET bolum = ?, vardiya = ?, servis_duragi = ?, telefon_no = ?, durum = 'AKTİF', gorev = ?
                    WHERE id = ?
                """, (role, shift, location, phone, role if role != "Personel" else "Personel", pid))
                # Note: Update gorev specifically if needed, using role as department/gorev
            else:
                # Insert
                print(f"Inserting {name}...")
                cursor.execute("""
                    INSERT INTO personnel (ad_soyad, bolum, gorev, vardiya, servis_duragi, telefon_no, durum)
                    VALUES (?, ?, ?, ?, ?, ?, 'AKTİF')
                """, (name, role, role, shift, location, phone))
                
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    update_db()
