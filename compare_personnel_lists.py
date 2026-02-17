import sqlite3
import difflib

# Extracted from images
main_list = [
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

def get_fuzzy_match(name, choices, threshold=0.7):
    matches = difflib.get_close_matches(name, choices, n=1, cutoff=threshold)
    return matches[0] if matches else None

def compare_personnel():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # Get current personnel
    cursor.execute("SELECT ad_soyad, bolum, id FROM personel WHERE durum = 'Aktif'")
    current_personnel = {row[0].strip().upper(): {"bolum": row[1], "id": row[2]} for row in cursor.fetchall()}
    
    all_new_names = {}
    for name in main_list: all_new_names[name.strip().upper()] = "EKLER" # Defaulting main list to EKLER as seen in context
    for name in rulo_pasta_list: all_new_names[name.strip().upper()] = "RULO PASTA"
    for name in bomba_list: all_new_names[name.strip().upper()] = "BOMBA"
    
    new_entries = []
    updates = []
    matches_seen = set()
    
    print("\n--- NEW PERSONNEL TO ADD ---")
    with open('comparison_output.txt', 'w', encoding='utf-8') as f:
        f.write("--- NEW PERSONNEL TO ADD ---\n")
        for name, bolum in all_new_names.items():
            match = get_fuzzy_match(name, current_personnel.keys())
            if not match:
                f.write(f"NEW: {name} -> {bolum}\n")
                new_entries.append((name, bolum))
            else:
                matches_seen.add(match)
                if current_personnel[match]["bolum"] != bolum:
                    f.write(f"UPDATE DEPT: {match} (Old: {current_personnel[match]['bolum']} -> New: {bolum})\n")
                    updates.append((current_personnel[match]["id"], bolum))

        f.write("\n--- PERSONNEL NOT IN NEW LIST (DELETION / INACTIVE?) ---\n")
        current_not_in_new = []
        for name, data in current_personnel.items():
            if name not in matches_seen:
                # Check fuzzy again from current to new
                fuzzy_back = get_fuzzy_match(name, all_new_names.keys())
                if not fuzzy_back:
                    f.write(f"MISSING: {name} | {data['bolum']} | ID: {data['id']}\n")
                    current_not_in_new.append((data['id'], name, data['bolum']))

    conn.close()
    return new_entries, updates, current_not_in_new

if __name__ == "__main__":
    compare_personnel()
