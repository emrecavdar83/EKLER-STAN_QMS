
import sqlite3
import pandas as pd
import re
from datetime import datetime

DB_PATH = 'ekleristan_local.db'
RAW_DATA_FILE = 'raw_personnel_data.txt'

SHIFT_MAP = {
    "07:00 / 15:00": "GÜNDÜZ VARDİYASI",
    "08:00 / 18:00": "GÜNDÜZ VARDİYASI",
    "07:00 / 15:03": "GÜNDÜZ VARDİYASI",
    "15:00 / 23:00": "GECE VARDİYASI",
}

MANAGERS = {
    "EMRE ÇAVDAR": {"rol": "Yönetim", "gorev": "KALİTE GÜVENCE MÜDÜRÜ"},
    "MUSTAFA AVŞAR": {"rol": "Yönetim", "gorev": "ÜRETİM MÜDÜRÜ"},
    "GAMZE AKCAN": {"rol": "Yönetim", "gorev": "GIDA MÜHENDİSİ"},
    "MEHMET ÖZGÜR": {"rol": "Yönetim", "gorev": "PLANLAMA YÖNETİCİSİ"},
    "HAKAN ÖZALP": {"rol": "Yönetim", "gorev": "EKİP SORUMLUSU"},
    "GÜLARA ŞEN": {"rol": "Yönetim", "gorev": "EKİP SORUMLUSU"}
}

def normalize_name(name):
    return name.upper().replace('İ','I').replace('Ğ','G').replace('Ü','U').replace('Ş','S').replace('Ö','O').replace('Ç','C').replace(' ','')

def parse_line(line):
    # Initial cleanup
    parts = line.strip().split()
    if not parts or not parts[0].isdigit(): return None
    
    # Extract Phone (Last token if 10+ digits)
    phone = ""
    if len(parts[-1]) >= 10 and parts[-1].isdigit(): 
        phone = parts.pop()
    
    # Reconstruct line without ID and Phone
    clean_line = " ".join(parts[1:])
    
    # Secondary Phone Regex (in case it wasn't the very last space-separated token)
    phone_match = re.search(r'\s(0?5\d{9})$', clean_line)
    if phone_match and not phone:
        phone = phone_match.group(1)
        clean_line = clean_line[:phone_match.start()].strip()
        
    shift_match = re.search(r'(\d{2}:\d{2}\s*/\s*\d{2}:\d{2})', clean_line)
    
    name = ""
    dept = ""
    shift = ""
    service = ""
    
    # Helper for department extraction
    known_depts = [
        "PROFİTEROL", "PANDİSPANYA", "FIRIN", "GENEL TEMİZLİK", "KREMA", "SOS", "BOMBA", 
        "RULO PASTA", "HALKA TATLI", "BULAŞIKHANE", "ET İŞLEME", "DEPO", "SEVKİYAT", 
        "EKİP SORUMLUSU", "BAKIM", "İ.K.", "SNOWLAND", "KALİTE MÜDÜRÜ", "KALİTE", "PLANLAMA", 
        "YÖNETİM", "İNSAN KAYNAKLARI", "ÜRETİM", "GIDA MÜH.", "İDARİ PERSONEL",
        "MÜDÜRÜ", "MÜH." # Fallback titles
    ]
    # Sort distinct known depts by length desc
    known_depts = sorted(list(set(known_depts)), key=len, reverse=True)

    # Strategy 1: Shift acts as separator
    if shift_match:
        shift = shift_match.group(1)
        before_shift = clean_line[:shift_match.start()].strip()
        service = clean_line[shift_match.end():].strip()
        
        # Extract Dept from Name (End of Name)
        best_dept = ""
        for d in known_depts:
            if before_shift.endswith(d):
                # Ensure it's not just a suffix of a name but a distinctive word if possible
                # But here it simplifies to just suffix
                if len(d) > len(best_dept):
                    best_dept = d
        
        if best_dept:
            dept = best_dept
            name = before_shift[:-len(dept)].strip()
        else:
            name = before_shift

    # Strategy 2: No Shift (Admin/Office Staff) -> Use Dept as separator
    else:
        found_dept = False
        for d in known_depts:
            # Look for department string with spaces around it or at end
            if d in clean_line:
                idx = clean_line.rfind(d) # Find last occurrence usually
                name = clean_line[:idx].strip()
                dept = d
                service = clean_line[idx+len(d):].strip()
                found_dept = True
                break
        
        if not found_dept:
            name = clean_line # Fallback
            
    return {"name": name, "department": dept, "shift": shift, "service": service, "phone": phone}


def smart_update():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Schema check (idempotent)
    try:
        cursor.execute("ALTER TABLE personel ADD COLUMN servis_duragi TEXT")
    except:
        pass
        
    try:
        cursor.execute("ALTER TABLE personel ADD COLUMN telefon_no TEXT")
    except:
        pass

    # Read Raw Data
    updates = []
    with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            p = parse_line(line)
            if p: updates.append(p)
            
    print(f"Loaded {len(updates)} personnel records for sync.")
    
    stats = {"inserted": 0, "updated": 0, "deleted": 0}
    
    # Pre-fetch existing personnel for faster lookup
    cursor.execute("SELECT id, ad_soyad, gorev, rol FROM personel")
    all_rows = cursor.fetchall()
    
    # Map normalized name to row
    db_map = {normalize_name(r[1]): r for r in all_rows}

    for p in updates:
        raw_name = p['name']
        dept = p['department']
        raw_shift = p['shift']
        service = p['service']
        phone = p['phone']
        
        # Map Shift
        mapped_shift = SHIFT_MAP.get(raw_shift, "GÜNDÜZ VARDİYASI" if "07:00" in raw_shift else ("GECE VARDİYASI" if "15:00" in raw_shift else raw_shift))
        if not mapped_shift: mapped_shift = "GÜNDÜZ VARDİYASI" # Default
            
        n_name = normalize_name(raw_name)
        
        if n_name in db_map:
            # UPDATE
            match_row = db_map[n_name]
            pid, current_name, current_gorev, current_rol = match_row
            
            new_gorev = current_gorev
            new_rol = current_rol
            
            # Special Manager Roles Override
            for mgr, details in MANAGERS.items():
                if normalize_name(mgr) in n_name: 
                    new_rol = details['rol']
                    new_gorev = details['gorev']
            
            cursor.execute("""
                UPDATE personel 
                SET bolum=?, vardiya=?, servis_duragi=?, telefon_no=?, gorev=?, rol=?, durum='AKTİF'
                WHERE id=?
            """, (dept, mapped_shift, service, phone, new_gorev, new_rol, pid))
            stats['updated'] += 1
            
        else:
            # INSERT
            rol = "Personel"
            gorev = "Personel"
            
            for mgr, details in MANAGERS.items():
                if normalize_name(mgr) in n_name:
                    rol = details['rol']
                    gorev = details['gorev']
            
            if dept and gorev == "Personel": gorev = f"{dept} Personel"
            
            cursor.execute("""
                INSERT INTO personel (ad_soyad, bolum, vardiya, servis_duragi, telefon_no, gorev, rol, durum, pozisyon_seviye)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'AKTİF', 5)
            """, (raw_name, dept, mapped_shift, service, phone, gorev, rol))
            stats['inserted'] += 1

    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM personel WHERE durum='AKTİF'")
    final_count = cursor.fetchone()[0]
    
    print("="*30)
    print("SENKRONİZASYON TAMAMLANDI (V2)")
    print(f"Yeni Eklenen: {stats['inserted']}")
    print(f"Güncellenen: {stats['updated']}")
    print(f"Toplam Aktif Personel: {final_count}")
    print("="*30)
    
    conn.close()

if __name__ == "__main__":
    smart_update()
