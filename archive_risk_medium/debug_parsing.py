
import re

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
            "MÜDÜRÜ", "MÜH." # Fallback titles
        ]
        
        best_dept = ""
        for d in known_depts:
            if before_shift.endswith(d):
                if len(d) > len(best_dept):
                    best_dept = d
        
        if best_dept:
            dept = best_dept
            name = before_shift[:-len(dept)].strip()
        else:
            name = before_shift

    # Strategy 2: No Shift (Admin/Office Staff) -> Use Dept as separator
    else:
        # Known Departments/Titles for admin staff
        known_depts = [
            "GIDA MÜH.", "KALİTE MÜDÜRÜ", "EKİP SORUMLUSU", "BAKIM", "DEPO", "İ.K.", "İDARİ PERSONEL",
            "KALİTE", "PLANLAMA", "ÜRETİM", "YÖNETİM", "GENEL MÜDÜR"
        ]
        
        # Sort by length desc to match longest first ("KALİTE MÜDÜRÜ" before "KALİTE")
        known_depts.sort(key=len, reverse=True)
        
        found_dept = False
        for d in known_depts:
            # Look for department string with spaces around it or at end
            # "NAME SURNAME DEPT SERVICE"
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

# Test Data
lines = [
    "1 ABDALRAOUF O A  BARGHOUTH PROFİTEROL 07:00 / 15:00 BEŞYOL - FATİH MAHALLESİ 5079717416",
    "2 ABDULDAYİM ABDURREZZAK PANDİSPANYA 07:00 / 15:00 DUAÇINARI 5364716254",
    "119 SEFER CAN ER BAKIM KENDİ GELİYOR",
    "161 GAMZE AKCAN GIDA MÜH. ÇEKİRGE MEYDAN 5324883867",
    "163 EMRE ÇAVDAR KALİTE MÜDÜRÜ KENDİ GELİYOR 5327920122"
]

print("-" * 50)
for l in lines:
    print(f"INPUT: {l}")
    print(f"PARSED: {parse_line(l)}")
    print("-" * 50)
