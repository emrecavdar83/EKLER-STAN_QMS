import sqlite3

def turkish_upper(s):
    if not s: return ""
    replace_map = {'i': 'İ', 'ı': 'I'}
    res = ""
    for char in s:
        res += replace_map.get(char, char.upper())
    return res.strip()

# EXACT names from images for the 3 departments
profiterol_list = [
    "Razen Albeder", "Alaa Mahsup", "Hasim Arif", "Duaa Khayat", "Aygül Ceylan",
    "Bilgen Yadam", "Yasmin Sakorya", "Abdulmolik barokot", "Şerife Deniz",
    "Cevler Demirden", "Kamuran Muratgil", "Oya Erdoğan", "Muhammet Massat",
    "Muhammet Fathi", "Kerima Akros", "Elif Tahtalı", "Özlem Yadam"
]

rulo_pasta_list = [
    "Mehriban Ali", "Zubale Mehti", "Zeynep Albayrak", "Zeynep Teber", "Esra Tarık",
    "Muhap Kahpevar", "Valid İbrahim", "Valid Elamro", "Çetin Deviren", "Burcu Şahin"
]

bomba_list = [
    "Gülay Mutlu", "Serap Ölger", "Fatma Öksüz", "Hamiyet Uymaz", "Muhammed Nur Bekei",
    "Ömer Salem", "Vechettin Güneş", "Zeynep Darendelioğlu", "Ümmühan Oruç", "Rümeysa Yaşar",
    "Maime Özdemir", "Ahmad Aburmh", "Aysel Aslan", "Olcay Yeşilyurt", "Eda Okçu Korkmaz",
    "Orhan Kalın", "Nuriye Atasay", "Seher Özatila", "Kübra Kutlu", "Feriha Gülten",
    "Rabia İbrahim Baş", "Hamza Ashran", "Telal Sefika"
]

def sync_all():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # 1. Gather all current names in DB (case-insensitive mapping)
    cursor.execute("SELECT id, ad_soyad, bolum, durum FROM personel")
    db_personnel = cursor.fetchall()
    
    # 2. Build map of existing people: upper_name -> (id, current_name, current_bolum)
    name_map = {}
    for p_id, name, bolum, durum in db_personnel:
        u_name = turkish_upper(name)
        if u_name not in name_map:
            name_map[u_name] = []
        name_map[u_name].append({'id': p_id, 'name': name, 'bolum': bolum, 'durum': durum})

    def find_best_match(target_name):
        u_target = turkish_upper(target_name)
        # Direct match
        if u_target in name_map:
            return name_map[u_target][0]
        # Common variations could be added here, but let's stick to what we have
        return None

    all_target_names = []
    
    # Process each list
    for dept, names in [("PROFİTEROL", profiterol_list), ("RULO PASTA", rulo_pasta_list), ("BOMBA", bomba_list)]:
        for name in names:
            all_target_names.append(turkish_upper(name))
            match = find_best_match(name)
            if match:
                # Update if name spelling or bolum is different
                if match['name'] != name or match['bolum'] != dept or match['durum'] != 'Aktif':
                    cursor.execute("UPDATE personel SET ad_soyad = ?, bolum = ?, durum = 'Aktif' WHERE id = ?", (name, dept, match['id']))
            else:
                # Add as new
                cursor.execute("INSERT INTO personel (ad_soyad, bolum, durum) VALUES (?, ?, 'Aktif')", (name, dept))

    # 3. Deactivate people in these 3 depts NOT in the target lists
    deactivated = []
    target_depts = ("PROFİTEROL", "RULO PASTA", "BOMBA")
    # Refresh DB state to see newly updated/added
    cursor.execute("SELECT id, ad_soyad, bolum FROM personel WHERE bolum IN (?, ?, ?) AND durum = 'Aktif'", target_depts)
    active_now = cursor.fetchall()
    
    for p_id, name, bolum in active_now:
        if turkish_upper(name) not in all_target_names:
            cursor.execute("UPDATE personel SET durum = 'Pasif' WHERE id = ?", (p_id,))
            deactivated.append(f"{name} ({bolum})")

    conn.commit()
    conn.close()
    
    with open('final_pasif_liste.txt', 'w', encoding='utf-8') as f:
        for item in deactivated:
            f.write(item + "\n")
            
    return deactivated

if __name__ == "__main__":
    list_pasif = sync_all()
    print(f"Pasif edilen {len(list_pasif)} kişi:")
    for p in list_pasif:
        print(p)
