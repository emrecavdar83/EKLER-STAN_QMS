import sqlite3

def apply_updates():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    updates_made = []
    
    # 1. New Personnel to Add
    # Table structure check from previous steps showed columns: (id, ad_soyad, bolum, ...)
    # I'll insert minimal data for new ones
    new_personnel = [
        ("ABDULMOLIK BAROKOT", "PROFİTEROL"),
        ("MUHAMMET FATHİ", "PROFİTEROL"),
        ("AHMAD ABURMH", "BOMBA")
    ]
    
    for name, bolum in new_personnel:
        try:
            cursor.execute("INSERT INTO personel (ad_soyad, bolum, durum) VALUES (?, ?, 'Aktif')", (name, bolum))
            updates_made.append(f"ADDED: {name} (Dept: {bolum})")
        except Exception as e:
            updates_made.append(f"ERROR ADDING {name}: {str(e)}")

    # 2. Personnel Updates (Spelling & Department)
    # Mapping from implementation plan
    name_and_dept_updates = [
        # Profiterol
        ("RAZAN ALBADER", "Razen Albeder", "PROFİTEROL"),
        ("ALAA MAHCUB", "Alaa Mahsup", "PROFİTEROL"),
        ("HAŞEM ARİF", "Hasim Arif", "PROFİTEROL"),
        ("BİLGEN YORDAM", "Bilgen Yadam", "PROFİTEROL"),
        ("YASEMİN SAKARYA", "Yasmin Sakorya", "PROFİTEROL"),
        ("GÜLER DEMİRDEN", "Cevler Demirden", "PROFİTEROL"),
        ("KERİME AKHRAS", "Kerima Akros", "PROFİTEROL"),
        ("ÖZLEM YORDAM", "Özlem Yadam", "PROFİTEROL"),
        ("MOHAMAD MASSAT", "Muhammet Massat", "PROFİTEROL"), # Move to Profiterol
        # Rulo Pasta
        ("MEHRİBAN ALİ", "Mehriban Ali", "RULO PASTA"), # Move to Rulo Pasta
        ("MOHAB KEBBEH WAR", "Muhap Kahpevar", "RULO PASTA"),
        ("VELİD ALAMRA", "Valid Elamro", "RULO PASTA"),
        # Bomba
        ("SERAP ÖZGER", "Serap Ölger", "BOMBA"),
        ("MUHAMMED NOR BEKRİ", "Muhammed Nur Bekei", "BOMBA"),
        ("OMAR SALEM", "Ömer Salem", "BOMBA"),
        ("NURİYE ATASOY", "Nuriye Atasay", "BOMBA"),
        ("FERİHA GÜLŞEN", "Feriha Gülten", "BOMBA")
    ]
    
    for old_name, new_name, new_bolum in name_and_dept_updates:
        try:
            # First find the person by name (case insensitive/trimmed)
            cursor.execute("SELECT id, ad_soyad, bolum FROM personel WHERE UPPER(TRIM(ad_soyad)) = ?", (old_name.upper(),))
            row = cursor.fetchone()
            if row:
                p_id = row[0]
                cursor.execute("UPDATE personel SET ad_soyad = ?, bolum = ?, durum = 'Aktif' WHERE id = ?", (new_name, new_bolum, p_id))
                updates_made.append(f"UPDATED: {old_name} -> {new_name} (Dept: {new_bolum})")
            else:
                updates_made.append(f"SKIP: {old_name} not found for update")
        except Exception as e:
            updates_made.append(f"ERROR UPDATING {old_name}: {str(e)}")

    # 3. Deactivate those NOT in the lists (Bomba, Profiterol, Rulo Pasta only)
    # The lists I have:
    all_current_names = [
        "Razen Albeder", "Alaa Mahsup", "Hasim Arif", "Duaa Khayat", "Aygül Ceylan",
        "Bilgen Yadam", "Yasmin Sakorya", "Abdulmolik barokot", "Şerife Deniz",
        "Cevler Demirden", "Kamuran Muratgil", "Oya Erdoğan", "Muhammet Massat",
        "Muhammet Fathi", "Kerima Akros", "Elif Tahtalı", "Özlem Yadam",
        "Mehriban Ali", "Zubale Mehti", "Zeynep Albayrak", "Zeynep Teber", "Esra Tarık",
        "Muhap Kahpevar", "Valid İbrahim", "Valid Elamro", "Çetin Deviren", "Burcu Şahin",
        "Gülay Mutlu", "Serap Ölger", "Fatma Öksüz", "Hamiyet Uymaz", "Muhammed Nur Bekei",
        "Ömer Salem", "Vechettin Güneş", "Zeynep Darendelioğlu", "Ümmühan Oruç", "Rümeysa Yaşar",
        "Maime Özdemir", "Ahmad Aburmh", "Aysel Aslan", "Olcay Yeşilyurt", "Eda Okçu Korkmaz",
        "Orhan Kalın", "Nuriye Atasay", "Seher Özatila", "Kübra Kutlu", "Feriha Gülten",
        "Rabia İbrahim Baş", "Hamza Ashran", "Telal Sefika"
    ]
    all_current_upper = [n.upper() for n in all_current_names]
    
    target_depts = ('BOMBA', 'PROFİTEROL', 'RULO PASTA')
    try:
        cursor.execute("SELECT id, ad_soyad, bolum FROM personel WHERE bolum IN (?, ?, ?) AND durum = 'Aktif'", target_depts)
        for p_id, ad_soyad, bolum in cursor.fetchall():
            if ad_soyad.upper().strip() not in all_current_upper:
                # Double check for common variations if needed, but the plan was approved
                cursor.execute("UPDATE personel SET durum = 'Pasif' WHERE id = ?", (p_id,))
                updates_made.append(f"DEACTIVATED: {ad_soyad} ({bolum})")
    except Exception as e:
        updates_made.append(f"ERROR DEACTIVATING: {str(e)}")

    conn.commit()
    conn.close()
    
    with open('execution_log.txt', 'w', encoding='utf-8') as f:
        for log in updates_made:
            f.write(log + '\n')
    
    print("\n".join(updates_made))

if __name__ == "__main__":
    apply_updates()
