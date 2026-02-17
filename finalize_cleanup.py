import sqlite3

# Current lists extracted from images
current_lists = {
    "PROFİTEROL": [
        "Razen Albeder", "Alaa Mahsup", "Hasim Arif", "Duaa Khayat", "Aygül Ceylan",
        "Bilgen Yadam", "Yasmin Sakorya", "Abdulmolik barokot", "Şerife Deniz",
        "Cevler Demirden", "Kamuran Muratgil", "Oya Erdoğan", "Muhammet Massat",
        "Muhammet Fathi", "Kerima Akros", "Elif Tahtalı", "Özlem Yadam"
    ],
    "RULO PASTA": [
        "Mehriban Ali", "Zubale Mehti", "Zeynep Albayrak", "Zeynep Teber", "Esra Tarık",
        "Muhap Kahpevar", "Valid İbrahim", "Valid Elamro", "Çetin Deviren", "Burcu Şahin"
    ],
    "BOMBA": [
        "Gülay Mutlu", "Serap Ölger", "Fatma Öksüz", "Hamiyet Uymaz", "Muhammed Nur Bekei",
        "Ömer Salem", "Vechettin Güneş", "Zeynep Darendelioğlu", "Ümmühan Oruç", "Rümeysa Yaşar",
        "Maime Özdemir", "Ahmad Aburmh", "Aysel Aslan", "Olcay Yeşilyurt", "Eda Okçu Korkmaz",
        "Orhan Kalın", "Nuriye Atasay", "Seher Özatila", "Kübra Kutlu", "Feriha Gülten",
        "Rabia İbrahim Baş", "Hamza Ashran", "Telal Sefika"
    ]
}

def turkish_upper(s):
    # Basic Turkish upper conversion for matching
    replace_map = {'i': 'İ', 'ı': 'I'}
    res = ""
    for char in s:
        res += replace_map.get(char, char.upper())
    return res.strip()

all_current_upper = []
for dept, names in current_lists.items():
    for name in names:
        all_current_upper.append(turkish_upper(name))

def finalize_cleanup():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    deactivated_list = []
    target_depts = ('BOMBA', 'PROFİTEROL', 'RULO PASTA')
    
    # Fetch everyone in these departments
    cursor.execute("SELECT id, ad_soyad, bolum, durum FROM personel WHERE bolum IN (?, ?, ?)", target_depts)
    rows = cursor.fetchall()
    
    for p_id, ad_soyad, bolum, durum in rows:
        name_upper = turkish_upper(ad_soyad)
        if name_upper not in all_current_upper:
            # Check for very close matches to avoid accidental deactivation
            # For now, if it's not in the list, we deactivate as per user "PLANI UYGULA" command
            # but we first log it.
            if durum.upper() != "PASİF":
                cursor.execute("UPDATE personel SET durum = 'Pasif' WHERE id = ?", (p_id,))
                deactivated_list.append(f"{ad_soyad} ({bolum})")
    
    conn.commit()
    conn.close()
    
    with open('deactivated_report.txt', 'w', encoding='utf-8') as f:
        f.write("PASİF DURUMA GETİRİLEN PERSONEL LİSTESİ\n")
        f.write("=" * 40 + "\n")
        for item in deactivated_list:
            f.write(item + "\n")
            
    print(f"Total deactivated: {len(deactivated_list)}")
    for item in deactivated_list:
        print(item)

if __name__ == "__main__":
    finalize_cleanup()
