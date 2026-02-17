import re
import sqlite3
import datetime

RAW_FILE = "raw_personnel_data.txt"
DB_PATH = "ekleristan_local.db"

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
    
    # Secondary Phone Regex (in case it wasn't the very last token)
    phone_match = re.search(r'\s(0?5\d{9})$', clean_line)
    if phone_match and not phone:
        phone = phone_match.group(1)
        clean_line = clean_line[:phone_match.start()].strip()
        
    shift_match = re.search(r'(\d{2}:\d{2}\s*/\s*\d{2}:\d{2})', clean_line)
    
    name = ""
    dept = ""
    shift = ""
    service = ""
    
    # Strategy 1: Shift acts as separator
    if shift_match:
        shift = shift_match.group(1)
        before_shift = clean_line[:shift_match.start()].strip()
        service = clean_line[shift_match.end():].strip()
        
        # Extract Dept from Name (End of Name)
        known_depts = [
            "PROFİTEROL", "PANDİSPANYA", "FIRIN", "GENEL TEMİZLİK", "KREMA", "SOS", "BOMBA", 
            "RULO PASTA", "HALKA TATLI", "BULAŞIKHANE", "ET İŞLEME", "DEPO", "SEVKİYAT", 
            "EKİP SORUMLUSU", "BAKIM", "İ.K.", "SNOWLAND", "KALİTE MÜDÜRÜ", "KALİTE", "PLANLAMA", 
            "YÖNETİM", "İNSAN KAYNAKLARI", "ÜRETİM", "GIDA MÜH.", "İDARİ PERSONEL", 
            "MÜDÜRÜ", "MÜH."
        ]
        
        best_dept = ""
        for d in known_depts:
            if before_shift.endswith(d):
                if len(d) > len(best_dept):
                    best_dept = d
        
        # Additional check for space before dept to avoid partial word match if needed
        # But "BARGHOUTH PROFİTEROL" -> "PROFİTEROL" is good.
        
        if best_dept:
            dept = best_dept
            name = before_shift[:-len(dept)].strip()
        else:
            name = before_shift
            dept = "BELİRSİZ" # Default if shift exists but dept not found in known list? Or just assume part of name?
            # Actually typically there is a department. Let's assume name is everything if no dept found?
            # Or maybe "FIRIN" is very common.

    # Strategy 2: No Shift (Admin/Office Staff) -> Use Dept as separator
    else:
        known_depts = [
            "GIDA MÜH.", "KALİTE MÜDÜRÜ", "EKİP SORUMLUSU", "BAKIM", "DEPO", "İ.K.", "İDARİ PERSONEL",
            "KALİTE", "PLANLAMA", "ÜRETİM", "YÖNETİM", "GENEL MÜDÜR"
        ]
        known_depts.sort(key=len, reverse=True)
        
        found_dept = False
        for d in known_depts:
            if d in clean_line:
                idx = clean_line.rfind(d)
                name = clean_line[:idx].strip()
                dept = d
                service = clean_line[idx+len(d):].strip()
                found_dept = True
                break
        
        if not found_dept:
            name = clean_line
            dept = "OFİS/DİĞER"
            
    return {
        "ad_soyad": name, 
        "bolum": dept, 
        "vardiya": shift, 
        "servis_duragi": service, 
        "telefon_no": phone,
        "durum": "AKTİF"
    }

def import_roster():
    print("Reading raw file...")
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count_new = 0
    count_update = 0
    
    print("-" * 50)
    for l in lines:
        data = parse_line(l)
        if not data: continue
        
        # Check if exists
        cursor.execute("SELECT id FROM personel WHERE ad_soyad = ?", (data["ad_soyad"],))
        res = cursor.fetchone()
        
        if res:
            # Update
            pid = res[0]
            cursor.execute("""
                UPDATE personel 
                SET bolum=?, vardiya=?, servis_duragi=?, telefon_no=?, durum='AKTİF'
                WHERE id=?
            """, (data["bolum"], data["vardiya"], data["servis_duragi"], data["telefon_no"], pid))
            count_update += 1
            # print(f"Updated: {data['ad_soyad']}")
        else:
            # Insert
            cursor.execute("""
                INSERT INTO personel (ad_soyad, bolum, vardiya, servis_duragi, telefon_no, durum)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data["ad_soyad"], data["bolum"], data["vardiya"], data["servis_duragi"], data["telefon_no"], "AKTİF"))
            count_new += 1
            print(f"Inserted: {data['ad_soyad']}")
            
    conn.commit()
    conn.close()
    
    print("-" * 50)
    print(f"Total Lines: {len(lines)}")
    print(f"Updates: {count_update}")
    print(f"Inserts: {count_new}")
    print("Done.")

if __name__ == "__main__":
    import_roster()
