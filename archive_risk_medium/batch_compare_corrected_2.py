import sqlite3

# Gerçek görsel verilerinden okunan isimler
names_to_check = [
    "ARZU SEVEN", "ASIM DURMUŞ", "ASUMAN GÜNGÖR", "ASYA YILMAZ",
    "ATİLLA DEMİR", "AVNİ KILIÇ", "AYHAN ÖZTÜRK", "AYKUT ÇETİN",
    "AYSEL YILDIZ", "AYŞE DEMİR", "AYŞEGÜL KAYA", "AYTEKİN AYDIN",
    "AZİZ KURT", "BAHAR GÜNEŞ", "BAHAR YILDIRIM", "BANU ERDOĞAN",
    "BARIŞ ARSLAN", "BAYRAM YAVUZ", "BEHLÜL ŞAHİN", "BEKİR UZUN"
]

def normalize_name(name):
    if not name: return ""
    return "".join(name.upper().split()).replace("İ", "I").replace("Ğ", "G").replace("Ü", "U").replace("Ş", "S").replace("Ö", "O").replace("Ç", "C")

def check_names():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ad_soyad FROM personel")
    db_names = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    
    normalized_db_names = {normalize_name(name): name for name in db_names}
    
    results = []
    for name in names_to_check:
        norm_name = normalize_name(name)
        if norm_name in normalized_db_names:
            results.append((name, "Eşleşti", normalized_db_names[norm_name]))
        else:
            results.append((name, "Eksik", "-"))
            
    print("| No | Görseldeki İsim | Durum | DB Kaydı |")
    print("|----|-----------------|-------|----------|")
    for i, (name, status, db_rec) in enumerate(results, 21):
        print(f"| {i} | {name} | {status} | {db_rec} |")

if __name__ == "__main__":
    check_names()
