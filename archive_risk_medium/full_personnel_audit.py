import sqlite3
import os
import sys

# Ensure stdout is safe (or at least try to)
def safe_print(s):
    try:
        print(s.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    except:
        print(s.encode('ascii', errors='replace').decode('ascii'))

# --- VERI LISTESI (1-176) --- (Extracted and normalized names in script)
raw_personnel = [
    (1, "ABDALRAOUF O A BARGHOUTH", "PROFITEROL", "BESYOL - FATIH MAHALLESI"),
    (2, "ABDULDAYIM ABDURREZZAK", "PANDISPANYA", "07:00 / 15:00"),
    (3, "ABDULHADI KURTAY", "FIRIN", "15:00 / 23:00"),
    (4, "ABDULKERIM MAGRIBI", "GENEL TEMIZLIK", ""),
    (5, "ABDULLAH ALHANZAL", "PANDISPANYA", "07:00 / 15:00"),
    (6, "ABDULMUHSIN HUDYER", "KREMA", "07:00 / 15:00"),
    (7, "ABDULRAHIM EID", "FIRIN", "15:00 / 23:00"),
    (8, "ABDULRAHMAN KALLAS", "FIRIN", "07:00 / 15:00"),
    (9, "ABDULRAHMAN SUKKAR", "FIRIN", "15:00 / 23:00"),
    (10, "ABDURRAHMAN ARAB", "BOMBA", "15:00 / 23:00"),
    (11, "AHMAD OLABI", "GENEL TEMIZLIK", ""),
    (12, "AHMAD KOURANI", "GENEL TEMIZLIK", ""),
    (13, "AHMAD KOURANI", "KREMA", "15:00 / 23:00"),
    (14, "AHMED EL MUSTAFA", "KREMA", "15:00 / 23:00"),
    (15, "AHMED MUHAMMED SEYFO", "FIRIN", "07:00 / 15:00"),
    (16, "AHMED BESSAR EIDO", "SOS", ""),
    (17, "AHMET SOLAKLI", "FIRIN", "07:00 / 15:00"),
    (18, "ALAA HARIRI", "PROFITEROL", ""),
    (19, "ALAA MAHCUB", "PROFITEROL", ""),
    (20, "ALAA ALNABHAN", "FIRIN", "15:00 / 23:00"),
    (21, "ALAA EDDIN NAJI", "PANDISPANYA", "07:00 / 15:00"),
    (22, "ALI SALEM", "FIRIN", "07:00 / 15:00"),
    (23, "ALI HAMDAN", "PANDISPANYA", "07:00 / 15:00"),
    (24, "ALICAN ALI", "RULO PASTA", ""),
    (25, "ANAS SKAFI", "KREMA", "15:00 / 23:00"),
    (26, "ASLI KAYA", "BOMBA", "15:00 / 23:00"),
    (27, "ATAKAN KAYA", "GENEL TEMIZLIK", ""),
    (28, "AYGUL CEYLAN", "PROFITEROL", ""),
    (29, "AYLA SARAC", "GENEL TEMIZLIK", ""),
    (30, "AYSE GITMEZ", "BULASIKHANE", ""),
    (31, "BATIKAN ARSLAN", "PROFITEROL", ""),
    (32, "BILGEN YORDAM", "PROFITEROL", ""),
    (33, "CELEL EL MAHFUZ", "FIRIN", "15:00 / 23:00"),
    (34, "CEMAL KOC", "DEPO", "08:00 / 18:00"),
    (35, "CEMAL ABDULNASIR ESMAIL", "PANDISPANYA", "07:00 / 15:00"),
    (36, "CETIN DEVIREN", "RULO PASTA", ""),
    (37, "DIAA SHBIB", "KREMA", "07:00 / 15:00"),
    (38, "DUAA KHAYAT", "PROFITEROL", ""),
    (39, "ELIF TAHTALI", "PROFITEROL", ""),
    (40, "ELVAN OZDEMIREL", "SOS", ""),
    (41, "EMINE SIZUCEN", "RULO PASTA", ""),
    (42, "EMIRHAN ALREZ", "FIRIN", "15:00 / 23:00"),
    (43, "EMRAH EKBER", "DEPO", ""),
    (44, "ERDAL OZTURK", "FIRIN", "07:00 / 15:00"),
    (45, "ERKAN DEMIR", "HALKA TATLI", ""),
    (46, "ESMIRA HALIL", "BULASIKHANE", ""),
    (47, "ESRA TARIK", "RULO PASTA", ""),
    (48, "EZEL ALRIHANI", "FIRIN", "07:00 / 15:00"),
    (49, "FERAS KANNI", "BULASIKHANE", ""),
    (50, "FERIHA GULSEN", "BOMBA", "07:00 / 15:00"),
    (51, "FIRDES TASAN", "GENEL TEMIZLIK", ""),
    (52, "GURBET KIYAR", "BOMBA", "15:00 / 23:00"),
    (53, "GULARA SEN", "EKIP SORUMLUSU", ""),
    (54, "GULAY MUTLU", "BOMBA", "07:00 / 15:00"),
    (55, "GULER DEMIRDEN", "PROFITEROL", ""),
    (56, "GULSEN NICE", "RULO PASTA", ""),
    (57, "HAFIZE ERGUTEKIN", "GENEL TEMIZLIK", ""),
    (58, "HAKAN OZALP", "EKIP SORUMLUSU", ""),
    (59, "HAKTAN CAKMAK", "SEVKIYAT", ""),
    (60, "HAMIYET UYMAZ", "BOMBA", "07:00 / 15:00"),
    (61, "HAMZA ASHRAM", "BOMBA", "07:00 / 15:00"),
    (62, "HAMZA KUTLU", "GENEL TEMIZLIK", ""),
    (63, "HANAA ELABDO", "BULASIKHANE", ""),
    (64, "HANIM ERKUL", "BULASIKHANE", ""),
    (65, "HASAN YILMAZ", "FIRIN", "15:00 / 23:00"),
    (66, "HASKIZ ERKUL", "BULASIKHANE", ""),
    (67, "HASSAN HABRA", "PANDISPANYA", "07:00 / 15:00"),
    (68, "HASSAN HABRA", "PANDISPANYA", "07:00 / 15:00"),
    (69, "HASEM ARIF", "PROFITEROL", ""),
    (70, "HATICE DIL", "GENEL TEMIZLIK", ""),
    (71, "HAYSAM KORANI", "PANDISPANYA", "07:00 / 15:00"),
    (72, "HOSSAM ALDIN ALTAHAN", "HALKA TATLI", "07:00 / 15:00"),
    (73, "HSAN KAFRNAWI", "FIRIN", "07:00 / 15:00"),
    (74, "HUSSAMALDEEN BAZARBASHI", "FIRIN", "07:00 / 15:00"),
    (75, "IBRAHIM KARKANDI", "FIRIN", "07:00 / 15:00"),
    (76, "IMADADDIN HAIK", "GENEL TEMIZLIK", ""),
    (77, "IBRAHIM KESIMOGLU", "FIRIN", "15:00 / 23:00"),
    (78, "ISMAIL OMEROĞLU", "HALKA TATLI", "07:00 / 15:00"),
    (79, "KADRI NOUSH", "FIRIN", "15:00 / 23:00"),
    (80, "KAMURAN MURATGIL", "PROFITEROL", ""),
    (81, "KERIME AKHRAS", "PROFITEROL", ""),
    (82, "KUBRA KUTLU", "BOMBA", "07:00 / 15:00"),
    (83, "MAHMOUD NASRALLAH", "KREMA", "07:00 / 15:00"),
    (84, "MAHMOUD KOURANI", "KREMA", "15:00 / 23:00"),
    (85, "MAHMOUD TAIR", "PANDISPANYA", "07:00 / 15:00"),
    (86, "MAHMUD SIDO", "FIRIN", "07:00 / 15:00"),
    (87, "MAIME OZDEMIR", "GENEL TEMIZLIK", ""),
    (88, "MAJED KHAYATA", "PANDISPANYA", "07:00 / 15:00"),
    (89, "MALIK SIMRECI", "RULO PASTA", ""),
    (90, "MEHRIBAN ALI", "RULO PASTA", ""),
    (91, "MHD MOAZ ALSAID", "SOS", ""),
    (92, "MHDIMADEDDIN ZAKRIA", "KREMA", "07:00 / 15:00"),
    (93, "MOHAB KEBBEH WAR", "RULO PASTA", ""),
    (94, "MOHAMAD AKKA", "GENEL TEMIZLIK", ""),
    (95, "MOHAMAD MASSAT", "PROFITEROL", ""),
    (96, "MOHAMAD SHAMMA", "GENEL TEMIZLIK", ""),
    (97, "MOHAMED KAMEL ELBANA", "KREMA", "15:00 / 23:00"),
    (98, "MUHAMED HAMAL", "PANDISPANYA", "07:00 / 15:00"),
    (99, "MUHAMMED KASSAB", "PANDISPANYA", "07:00 / 15:00"),
    (100, "MUHAMMED ELMUHAMMED", "GENEL TEMIZLIK", ""),
    (101, "MUHAMMED ZUHEYR MAGRIBI", "FIRIN", "15:00 / 23:00"),
    (102, "MUHANNED CEBBULI", "GENEL TEMIZLIK", ""),
    (103, "MUSTAFA GASIM", "FIRIN", "07:00 / 15:00"),
    (104, "MUSTAFA AVSAR", "IDARI PERSONEL", ""),
    (105, "MUNEVVER CETIN", "BULASIKHANE", ""),
    (106, "NERMIN DEMIR", "BULASIKHANE", ""),
    (107, "NESRIN ADA", "BOMBA", "07:00 / 15:00"),
    (108, "NIDAL ALALI", "PROFITEROL", ""),
    (109, "NURETTIN SOLAKLI", "FIRIN", "07:00 / 15:00"),
    (110, "NURIYE ATASOY", "BOMBA", "07:00 / 15:00"),
    (111, "OMAR SALEM", "BOMBA", "07:00 / 15:00"),
    (112, "OYA ERDOGAN", "PROFITEROL", ""),
    (113, "OZLEM YORDAM", "PROFITEROL", ""),
    (114, "RAZAN ALBADER", "PROFITEROL", ""),
    (115, "RECEP SOLAKLI", "FIRIN", "07:00 / 15:00"),
    (116, "RIDVAN KURTAY", "FIRIN", "07:00 / 15:00"),
    (117, "SAAD HABRA", "KREMA", "07:00 / 15:00"),
    (118, "SAID ABDULBAKI", "PANDISPANYA", "07:00 / 15:00"),
    (119, "SAIME TOPRAK", "BOMBA", "07:00 / 15:00"),
    (120, "SEFER CAN ER", "BAKIM", ""),
    (121, "SEHER OZATILA", "BOMBA", "07:00 / 15:00"),
    (122, "SELIM ARSLANTURK", "BAKIM", ""),
    (123, "SEMRA YILDIRIM", "PANDISPANYA", "07:00 / 15:00"),
    (124, "SENA KENNO", "BULASIKHANE", ""),
    (125, "SERKAN OZYUREK", "KREMA", "07:00 / 15:00"),
    (126, "SERKAN BEY", "FIRIN", "07:00 / 15:00"),
    (127, "SUDE OZBAYRAK", "I.K.", ""),
    (128, "SULEYMAN SIDO", "FIRIN", "07:00 / 15:00"),
    (129, "SEHRIYE YASAR", "RULO PASTA", ""),
    (130, "SERAFEDDIN SOZEN", "FIRIN", "07:00 / 15:00"),
    (131, "SERIFE DENIZ", "PROFITEROL", ""),
    (132, "TALIP BELLURA", "PROFITEROL", ""),
    (133, "TAYFUN KAYNAR", "DEPO", ""),
    (134, "TELAL SAKIFA", "BOMBA", "07:00 / 15:00"),
    (135, "UGUR UNLUSOY", "PANDISPANYA", "07:00 / 15:00"),
    (136, "UMUT ALACA", "RULO PASTA", ""),
    (137, "UMUT CAN KURTAY", "FIRIN", "15:00 / 23:00"),
    (138, "UMMUHAN ORUC", "BOMBA", "07:00 / 15:00"),
    (139, "UNZILE OZEL", "BULASIKHANE", ""),
    (140, "VAGIF MEHDI", "HALKA TATLI", "07:00 / 15:00"),
    (141, "YAMEN KENAAN", "KREMA", "07:00 / 15:00"),
    (142, "YASEMIN SAKARYA", "PROFITEROL", ""),
    (143, "YASER HAVCEH", "KREMA", "15:00 / 23:00"),
    (144, "ZEYNEP ALBAYRAK", "RULO PASTA", ""),
    (145, "ZILAL EL REMMO", "BULASIKHANE", ""),
    (146, "ZUBALA MEHDI", "RULO PASTA", ""),
    (147, "ZULFUYE CETIN", "BULASIKHANE", ""),
    (148, "ORHAN KALIN", "BOMBA", "07:00 / 15:00"),
    (149, "FATMA OKSUZ", "BOMBA", "07:00 / 15:00"),
    (150, "RUMEYSA YASAR", "BOMBA", "07:00 / 15:00"),
    (151, "VECHETTIN GUNES", "BOMBA", "07:00 / 15:00"),
    (152, "RABIA IBRAHIMBAS", "BOMBA", "07:00 / 15:00"),
    (153, "BILAL ANTAKLI", "BOMBA", "15:00 / 23:00"),
    (154, "HURMA DENLIYEVA", "PROFITEROL", ""),
    (155, "VELID ALAMRA", "RULO PASTA", ""),
    (156, "VELID IBRAHIM", "RULO PASTA", ""),
    (157, "YAHYA ALKAN", "FIRIN", "15:00 / 23:00"),
    (158, "NEVRAZ ALNASRI", "FIRIN", "15:00 / 23:00"),
    (159, "YELIZ CAKIR", "BOMBA", "07:00 / 15:00"),
    (160, "SAMIA HAG ALII", "BULASIKHANE", ""),
    (161, "GAMZE AKCAN", "GIDA MUH.", ""),
    (162, "MEHMET OZGUR", "GIDA MUH.", ""),
    (163, "EMRE CAVDAR", "KALITE MUDURU", ""),
    (164, "HAVVA ILBUS", "KREMA", "07:00 / 15:00"),
    (165, "AYSE KARAGOZ", "KREMA", "07:00 / 15:01"),
    (166, "SUNA YILDIZ", "KREMA", "07:00 / 15:02"),
    (167, "NACIYE", "KREMA", "07:00 / 15:03"),
    (168, "AISE KILINC", "KREMA", "07:00 / 15:04"),
    (169, "SEVGI ISLAM", "KREMA", "07:00 / 15:05"),
    (170, "ALAA OBAI", "FIRIN", "07:00 / 15:05"),
    (171, "ELIF ISIK", "FIRIN", "07:00 / 15:05"),
    (172, "GULAY GEM", "ET ISLEME", "07:00 / 15:05"),
    (173, "OSAMA FEDDO", "ET ISLEME", "07:00 / 15:05"),
    (174, "AHMAD KALLAJO", "ET ISLEME", "07:00 / 15:05"),
    (175, "SONGUL ERDAL", "ET ISLEME", "07:00 / 15:05"),
    (176, "TURGAY BARUTCU", "ET ISLEME", "07:00 / 15:05"),
]

def normalize(s):
    if not s: return ""
    s = str(s).upper().replace(" ", "")
    s = s.replace("I", "I").replace("İ", "I").replace("Ğ", "G").replace("Ü", "U").replace("Ş", "S").replace("Ö", "O").replace("Ç", "C")
    return s

def run_audit():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT ad_soyad, bolum, vardiya FROM personel")
    db_rows = cursor.fetchall()
    db_data = {normalize(row[0]): {"raw_name": row[0], "bolum": row[1], "vardiya": row[2]} for row in db_rows if row[0]}
    
    missing_sql = []
    total_count = len(raw_personnel)
    chunk_size = 20
    
    safe_print(f"--- PERSONNEL AUDIT REPORT ({total_count} entries) ---")
    
    for i in range(0, total_count, chunk_size):
        chunk = raw_personnel[i:i+chunk_size]
        matches = 0
        diffs = []
        missing = []
        
        for sno, name, dept, shift in chunk:
            norm_name = normalize(name)
            if norm_name in db_data:
                db_item = db_data[norm_name]
                has_diff = False
                diff_msg = []
                
                if dept and db_item['bolum'] and normalize(dept) != normalize(db_item['bolum']):
                    has_diff = True
                    diff_msg.append(f"Dept: {db_item['bolum']} vs {dept}")
                
                if shift and db_item['vardiya'] and normalize(shift) != normalize(db_item['vardiya']):
                    has_diff = True
                    diff_msg.append(f"Shift: {db_item['vardiya']} vs {shift}")
                
                if has_diff:
                    diffs.append(f"[DIFF] {name} ({', '.join(diff_msg)})")
                else:
                    matches += 1
            else:
                missing.append(f"[MISSING] {name} (Dept: {dept}, Shift: {shift})")
                missing_sql.append((name, dept, shift))
        
        safe_print(f"\n[BATCH {(i//chunk_size)+1}] ({i+1}-{min(i+chunk_size, total_count)})")
        safe_print(f"[OK] {matches} personnel matched perfectly.")
        
        for d in diffs: safe_print(d)
        for m in missing: safe_print(m)
                
    if missing_sql:
        if not os.path.exists('sql'): os.makedirs('sql')
        with open('sql/missing_personnel.sql', 'w', encoding='utf-8') as f:
            f.write("-- MISSING PERSONNEL IMPORT --\n")
            for name, dept, shift in missing_sql:
                f.write(f"INSERT INTO personel (ad_soyad, bolum, vardiya, durum) VALUES ('{name}', '{dept}', '{shift}', 'AKTIF');\n")
        safe_print(f"\n[DONE] sql/missing_personnel.sql generated ({len(missing_sql)} missing).")

    conn.close()

if __name__ == "__main__":
    run_audit()
