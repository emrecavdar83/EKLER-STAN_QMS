import sqlite3
import re

def normalize(name):
    if not name: return ""
    name = str(name).upper().strip()
    tr_map = str.maketrans("İĞÜŞÖÇ", "IGUSOC")
    name = name.translate(tr_map)
    return re.sub(r'[^A-Z0-9]', '', name)

def sync_perfectly():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    print("--- NİHAİ PERSONEL SENKRONİZASYONU (V2 - 182 HEDEF) ---")
    
    master_list = []
    with open('personnel_update_20260131.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:]
        for line in lines:
            if not line.strip(): continue
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                name = parts[1]
                dept = parts[2] if len(parts) > 2 else ""
                vardiya = parts[3] if len(parts) > 3 else ""
                servis = parts[4] if len(parts) > 4 else ""
                tel = parts[5] if len(parts) > 5 else ""
                
                master_list.append({
                    'name': name, 'dept': dept, 'vardiya': vardiya, 
                    'servis': servis, 'tel': tel, 'norm': normalize(name)
                })
    
    print(f"Master Listede {len(master_list)} kayıt yüklendi.")
    cursor.execute("UPDATE personel SET durum = 'PASİF'")
    
    cursor.execute("SELECT id, ad_soyad FROM personel")
    db_map = {normalize(r[1]): r[0] for r in cursor.fetchall()}
    
    processed_norms = set()
    matches, inserts = 0, 0

    for m in master_list:
        n = m['norm']
        if not n: continue
        if n in processed_norms: continue
        processed_norms.add(n)
        
        if n in db_map:
            cursor.execute("""
                UPDATE personel SET ad_soyad=?, bolum=?, vardiya=?, servis_duragi=?, telefon_no=?, durum='AKTİF'
                WHERE id=?
            """, (m['name'], m['dept'], m['vardiya'], m['servis'], m['tel'], db_map[n]))
            matches += 1
        else:
            cursor.execute("""
                INSERT INTO personel (ad_soyad, bolum, vardiya, servis_duragi, telefon_no, durum, pozisyon_seviye, rol, gorev)
                VALUES (?, ?, ?, ?, ?, 'AKTİF', 5, 'Personel', ?)
            """, (m['name'], m['dept'], m['vardiya'], m['servis'], m['tel'], f"{m['dept']} Personel"))
            inserts += 1

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM personel WHERE durum = 'AKTİF'")
    print(f"Sonuç: {cursor.fetchone()[0]} aktif personel (Hedef: 182).")
    conn.close()

if __name__ == "__main__":
    sync_perfectly()
