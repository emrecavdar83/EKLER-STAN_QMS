
import re

def parse_line(line):
    # Regex pattern:
    # ^(\d+)\s+             -> Start with ID number and whitespace
    # (.+?)                 -> Name (lazy match)
    # \s+                   -> Whitespace
    # (PROFİTEROL|PANDİSPANYA|FIRIN|GENEL TEMİZLİK|KREMA|SOS|BOMBA|RULO PASTA|HALKA TATLI|BULAŞIKHANE|ET İŞLEME|DEPO|SEVKİYAT|EKİP SORUMLUSU|BAKIM|İ\.K\.|SNOWLAND|KALİTE|PLANLAMA|YÖNETİM|İNSAN KAYNAKLARI|ÜRETİM|GIDA MÜH\.|İDARİ PERSONEL) -> Department (Known keywords)
    # \s+                   -> Whitespace
    # (\d{2}:\d{2}\s*/\s*\d{2}:\d{2})? -> Optional Shift
    # \s*                   -> Optional whitespace
    # (.*?)                 -> Service Stop (greedy until phone)
    # \s*                   -> Optional whitespace
    # (0?5\d{9})?           -> Optional Phone (Starts with 5 or 05, 10 digits)
    # \s*$                  -> End of line
    
    # Actually, regex is hard because Departments can be multi-word and Service text is free form.
    # Let's try right-to-left parsing.
    
    parts = line.strip().split()
    if not parts or not parts[0].isdigit():
        return None
        
    sno = parts[0]
    
    # Phone is usually last and looks like a number > 9 digits
    phone = ""
    if len(parts[-1]) >= 10 and parts[-1].isdigit():
        phone = parts.pop()
    
    # Shift is strictly HH:MM / HH:MM format
    shift_index = -1
    shift = ""
    for i, p in enumerate(parts):
        if '/' in p and ':' in p: # 07:00 / 15:00 (parts: 07:00, /, 15:00 or 07:00/15:00)
            # It's usually "07:00 / 15:00" -> 3 parts
            pass

    # Re-assemble string to regex properly
    clean_line = " ".join(parts[1:]) # Skip SNO
    
    # Find Phone at end
    phone_match = re.search(r'\s(0?5\d{9})$', clean_line)
    if phone_match:
        phone = phone_match.group(1)
        clean_line = clean_line[:phone_match.start()].strip()
        
    # Find Shift (HH:MM / HH:MM)
    shift_match = re.search(r'(\d{2}:\d{2}\s*/\s*\d{2}:\d{2})', clean_line)
    shift = ""
    if shift_match:
        shift = shift_match.group(1)
        # Split by shift
        start_idx = shift_match.start()
        end_idx = shift_match.end()
        
        name_part = clean_line[:start_idx].strip()
        service_part = clean_line[end_idx:].strip()
    else:
        # No shift? 
        # Case: 162 MEHMET ÖZGÜR GIDA MÜH. KENDİ GELİYOR 5454393078
        # "GIDA MÜH." is dept. "KENDİ GELİYOR" is service.
        # Fallback split
        name_part = clean_line
        service_part = ""

    # Name Part extraction
    # Name part contains Name + Dept.
    # Depts are known.
    known_depts = [
        "PROFİTEROL", "PANDİSPANYA", "FIRIN", "GENEL TEMİZLİK", "KREMA", "SOS", "BOMBA", 
        "RULO PASTA", "HALKA TATLI", "BULAŞIKHANE", "ET İŞLEME", "DEPO", "SEVKİYAT", 
        "EKİP SORUMLUSU", "BAKIM", "İ.K.", "SNOWLAND", "KALİTE MÜDÜRÜ", "KALİTE", "PLANLAMA", 
        "YÖNETİM", "İNSAN KAYNAKLARI", "ÜRETİM", "GIDA MÜH.", "İDARİ PERSONEL"
    ]
    
    dept = ""
    name = name_part
    
    # Try longest match for dept at end of name_part
    best_dept = ""
    for d in known_depts:
        if name_part.endswith(d):
            if len(d) > len(best_dept):
                best_dept = d
                
    if best_dept:
        dept = best_dept
        name = name_part[:-len(dept)].strip()
    else:
        # Some rows might not have dept in this column?
        # e.g. "8 B FIRIN" -> Name B, Dept FIRIN
        pass

    return {
        "sno": sno,
        "name": name,
        "department": dept,
        "shift": shift,
        "service": service_part,
        "phone": phone
    }

def main():
    data = []
    with open('raw_personnel_data.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parsed = parse_line(line)
            if parsed:
                data.append(parsed)
                
    # Generate Markdown Report
    print(f"Parsed {len(data)} records.")
    
    md = "# Proposed Personnel Updates\n\n"
    md += "| S.No | Name | Department | Shift | Service Stop | Phone |\n"
    md += "|---|---|---|---|---|---|\n"
    
    for row in data:
        md += f"| {row['sno']} | {row['name']} | {row['department']} | {row['shift']} | {row['service']} | {row['phone']} |\n"
        
    with open('proposed_personnel_updates.md', 'w', encoding='utf-8') as f:
        f.write(md)

    print("Report generated: proposed_personnel_updates.md")

if __name__ == "__main__":
    main()
