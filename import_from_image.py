import pandas as pd
from sqlalchemy import create_engine, text

# 1. VERİ LİSTESİ (Manual Transcription from Image)
# Format: (Ad Soyad, Bölüm, Yönetici)
raw_data = [
    ("ABDULRAOUF O A BARGHOUTH", "PROFİTEROL", "BATIKAN ASLAN"),
    ("ABDULDAYİM ABDURREZZAK", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ABDULHADİ KURTAY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDULLAH ALHANZAL", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ABDULRAHİM EİD", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDULRAHMAN KALLAS", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDULRAHMAN SUKKAR", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDURRAHMAN ARAB", "DOMBA", "YELİZ ÇAKIR"),
    ("AHMED MUHAMMED SEYİD", "PATAŞU", "NURETTİN SOLAKLI"),
    ("AHMET SOLAKLI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ALAA HARİRİ", "PROFİTEROL", "BATIKAN ASLAN"),
    ("ALAA MAHCUB", "PROFİTEROL", "BATIKAN ASLAN"),
    ("ALAA ALNARHAN", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ALAA EDDİN NALİ", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ALİ SALEM", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ALİ HAMDAN", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ALİCAN ALİ", "RULO PASTA", "MİHRİBAN ALİ"),
    ("ASLI KAYA", "BOMBA", "YELİZ ÇAKIR"),
    ("AYGÜL CEYLAN", "PROFİTEROL", "BATIKAN ASLAN"),
    ("BATIKAN ARSLAN", "PROFİTEROL", "BATIKAN ASLAN"), # Supervisor Self
    ("BİLGEN YORDAM", "PROFİTEROL", "BATIKAN ASLAN"),
    ("CELAL EL MAHFUZ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("CEMAL ABDULNASIR İSMAİL", "PANDİSPANYA", "CEMAL İSMAİL"), # Supervisor Self (CEMAL İSMAİL)
    ("ÇETİN DEVİREN", "RULO PASTA", "MİHRİBAN ALİ"),
    ("DUAA KHAYAT", "PROFİTEROL", "BATIKAN ASLAN"),
    ("ELİF TAHTALI", "PROFİTEROL", "BATIKAN ASLAN"),
    ("EMİNE SÜZÜĞEN", "RULO PASTA", "MİHRİBAN ALİ"),
    ("EMİRHAN ALREZ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ERDAL ÖZTÜRK", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ERKAN DEMİR", "HALKA TATLI", "ERKAN DEMİR"), # Supervisor Self
    ("ESRA TARIK", "RULO PASTA", "MİHRİBAN ALİ"),
    ("EZEL ALRHANI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("FATMA GÜLŞEN", "BOMBA", "YELİZ ÇAKIR"),
    ("GURBET KIYAR", "BOMBA", "YELİZ ÇAKIR"),
    ("GÜLAY MUTLU", "BOMBA", "YELİZ ÇAKIR"),
    ("GÜLER DEMİRDEN", "PROFİTEROL", "BATIKAN ASLAN"),
    ("GÜLŞEN NİCE", "RULO PASTA", "MİHRİBAN ALİ"),
    ("HAMİYET UYMAZ", "BOMBA", "YELİZ ÇAKIR"),
    ("HAMZA ASHEM", "DOMBA", "YELİZ ÇAKIR"),
    ("HASAN YILMAZ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("HASSAN HABRA", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("HAŞEM ARİF", "PROFİTEROL", "BATIKAN ASLAN"),
    ("HAYSAM KORANİ", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("HOSSAM ALDIN ALTAHAN", "HALKA TATLI", "ERKAN DEMİR"),
    ("İHSAN KAFKIRAN", "PATAŞU", "NURETTİN SOLAKLI"),
    ("HUSSAMALDEEN BAZARBASHI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İBRAHİM KAKİRANDİ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İBRAHİM KERİMOĞLU", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İSMAİL ÖMEROĞLU", "HALKA TATLI", "ERKAN DEMİR"),
    ("KADRİ NOUSH", "PATAŞU", "NURETTİN SOLAKLI"),
    ("KAMURAN MURATGİL", "PROFİTEROL", "BATIKAN ASLAN"),
    ("KERİME AKBAŞ", "PROFİTEROL", "BATIKAN ASLAN"),
    ("KÜBRA KUTLU", "BOMBA", "YELİZ ÇAKIR"),
    ("MAHMOUD TAIR", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("MAHMUD SİDO", "PATAŞU", "NURETTİN SOLAKLI"),
    ("MAJED KHAYATA", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("MALİK ŞİMRECİ", "RULO PASTA", "MİHRİBAN ALİ"),
    ("MİHRİBAN ALİ", "RULO PASTA", "MİHRİBAN ALİ"), # Supervisor Self
    ("MOHAB KEBBEH WAR", "RULO PASTA", "MİHRİBAN ALİ"),
    ("MUHAMED HAMAL", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("MUHAMMED KASSAB", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("MUHAMMED ZÜHEYR MAĞHİNİ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("MUSTAFA GAŞİM", "PATAŞU", "NURETTİN SOLAKLI"),
    ("NESRİN ADA", "DOMBA", "YELİZ ÇAKIR"),
    ("NİDAL ALAU", "PROFİTEROL", "BATIKAN ASLAN"),
    ("NURETTİN SOLAKLI", "PATAŞU", "NURETTİN SOLAKLI"), # Supervisor Self
    ("NURİYE ATASOY", "BOMBA", "YELİZ ÇAKIR"),
    ("OMAR SALEM", "BOMBA", "YELİZ ÇAKIR"),
    ("OYA ERDOĞAN", "PROFİTEROL", "BATIKAN ASLAN"),
    ("ÖZLEM YORDAM", "PROFİTEROL", "BATIKAN ASLAN"),
    ("RECEP SOLAKLI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("RIDVAN KURTAY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("SAİD ABDULBAKİ", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("SAİME TOPRAK", "BOMBA", "YELİZ ÇAKIR"),
    ("SEHER ÖZATLI", "BOMBA", "YELİZ ÇAKIR"),
    ("SEMRA YILDIRIM", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("SERKAN BEY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("SULEYMAN SİDO", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ŞEHRİYE YAŞAR", "RULO PASTA", "MİHRİBAN ALİ"),
    ("ŞERAFEDDİN SÖZEN", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ŞERİFE DENİZ", "PROFİTEROL", "BATIKAN ASLAN"),
    ("TALİP BELLURA", "PROFİTEROL", "BATIKAN ASLAN"),
    ("TELAL ŞAKİRA", "BOMBA", "YELİZ ÇAKIR"),
    ("UĞUR ÜNLÜSOY", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("UMUT ALACA", "RULO PASTA", "MİHRİBAN ALİ"),
    ("UMUT CAN KURTAY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ÜMMÜHAN ORUÇ", "BOMBA", "YELİZ ÇAKIR"),
    ("VAGIF MEHDİ", "HALKA TATLI", "ERKAN DEMİR"),
    ("YASEMİN SAKARYA", "PROFİTEROL", "BATIKAN ASLAN"),
    ("ZEYNEP ALBAYRAK", "RULO PASTA", "MİHRİBAN ALİ"),
    ("ZÜHALA MEHDİ", "RULO PASTA", "MİHRİBAN ALİ"),
    ("ORHAN KALIN", "BOMBA", "YELİZ ÇAKIR"),
    ("FATMA ÖKSÜZ", "BOMBA", "YELİZ ÇAKIR"),
    ("RÜMEYSA YAŞAR", "BOMBA", "YELİZ ÇAKIR"),
    ("VECHETTİN GÜNEŞ", "BOMBA", "YELİZ ÇAKIR"),
    ("FADİA İBRAHİM BAŞ", "BOMBA", "YELİZ ÇAKIR"),
    ("BİLAL ANTAKİ", "BOMBA", "YELİZ ÇAKIR"),
    ("HURMA DANLIYEVA", "PROFİTEROL", "BATIKAN ASLAN"),
    ("VELED ALAMRA", "RULO PASTA", "MİHRİBAN ALİ"),
    ("VELED İBRAHİM", "RULO PASTA", "MİHRİBAN ALİ"),
    ("YAHYA ALKAN", "PATAŞU", "NURETTİN SOLAKLI"),
    ("NEVRAZ ALNASRI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("YELİZ ÇAKIR", "BOMBA", "YELİZ ÇAKIR") # Supervisor Self
]

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    
    # 2. ÖNCE YENİ BÖLÜMLERİ OLUŞTUR
    needed_depts = ["DOMBA", "RULO PASTA", "HALKA TATLI", "PANDİSPANYA", "PROFİTEROL", "BOMBA", "PATAŞU"]
    
    with engine.connect() as conn:
        print("--- Departman Kontrolü ---")
        existing_depts = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", conn)
        dept_map = {row['bolum_adi']: row['id'] for _, row in existing_depts.iterrows()}
        
        # PANDİSPANYA fix (Kek -> Pandispanya migration might handle it, but being safe)
        
        for d in needed_depts:
            if d not in dept_map:
                print(f"Creating missing department: {d}")
                conn.execute(text("INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no) VALUES (:n, 1, 99)"), {"n": d})
                conn.commit() # Commit immediately to get ID
                
                # Fetch new ID
                new_id = conn.execute(text("SELECT id FROM ayarlar_bolumler WHERE bolum_adi = :n"), {"n": d}).scalar()
                dept_map[d] = new_id
            else:
                print(f"Department exists: {d} (ID: {dept_map[d]})")
        
        # 3. YÖNETİCİLERİ OLUŞTUR (SEVİYE 5 - Şef)
        supervisors = list(set([x[2] for x in raw_data]))
        # Map supervisor names to DB names (Handle partial matches if needed, but assuming full match)
        # Note: "CEMAL İSMAİL" matches "CEMAL ABDULNASIR İSMAİL" probably? No, treat as separate if distinct.
        # But in the list, row 23 is "CEMAL ABDULNASIR İSMAİL", sup is "CEMAL İSMAİL".
        # Assume "CEMAL İSMAİL" is the short name, likely the same person.
        # I will Create "CEMAL İSMAİL" if distinct.
        
        print("\n--- Yönetici Kontrolü ---")
        existing_pers = pd.read_sql("SELECT id, ad_soyad FROM personel", conn)
        pers_map = {row['ad_soyad']: row['id'] for _, row in existing_pers.iterrows()}
        
        # Supervisors mapping
        # Handle aliases: "BATIKAN ASLAN" (Image) -> "BATIKAN ARSLAN" (DB)
        # "HURMA DANLIYEVA" (Image) -> "HURMA DELİYEVA" (DB)? DB has "HURMA DELİYEVA"? Let's check.
        # DB has "HURMA DELİYEVA" (ID 215). Image has "HURMA DANLIYEVA". I'll assume match.
        
        aliases = {
            "BATIKAN ASLAN": "BATIKAN ARSLAN",
            "HURMA DANLIYEVA": "HURMA DELİYEVA"
        }

        sup_id_map = {}
        for sup_name in supervisors:
            # Check aliases
            search_name = aliases.get(sup_name, sup_name)
            
            # Check exist
            if search_name in pers_map:
                sup_id_map[sup_name] = pers_map[search_name]
                # Ensure level is at least 5?
                conn.execute(text("UPDATE personel SET pozisyon_seviye = 5 WHERE id = :id AND pozisyon_seviye > 5"), {"id": pers_map[search_name]})
                conn.commit()
            else:
                # Create Superior
                print(f"Creating NEW Supervisor: {sup_name}")
                # Create with dummy department (Managed later)
                conn.execute(text("INSERT INTO personel (ad_soyad, gorev, durum, pozisyon_seviye, departman_id) VALUES (:n, 'Bölüm Sorumlusu', 'AKTİF', 5, 1)"), {"n": sup_name})
                conn.commit()
                new_id = conn.execute(text("SELECT id FROM personel WHERE ad_soyad = :n"), {"n": sup_name}).scalar()
                pers_map[sup_name] = new_id
                sup_id_map[sup_name] = new_id

        # 4. PERSONEL İÇE AKTAR
        print("\n--- Personel İçe Aktarma ---")
        count = 0
        for name, dept_name, sup_name in raw_data:
            # Check aliases for Name too
            real_name = aliases.get(name, name)
            
            if real_name in pers_map:
                print(f"Skipping existing: {real_name}")
                # Optional: Update department/supervisor
                d_id = dept_map.get(dept_name, 1)
                s_id = sup_id_map.get(sup_name, 0)
                # print(f"Updating info for {real_name}")
                # conn.execute(text("UPDATE personel SET departman_id=:d, yonetici_id=:y WHERE id=:id"), {"d":d_id, "y":s_id, "id":pers_map[real_name]})
                # conn.commit()
            else:
                d_id = dept_map.get(dept_name, 1) # Default 1 if not found
                s_id = sup_id_map.get(sup_name, 0) # Default 0
                
                print(f"Inserting: {real_name} -> {dept_name}")
                conn.execute(text("""
                    INSERT INTO personel (ad_soyad, gorev, durum, pozisyon_seviye, departman_id, yonetici_id) 
                    VALUES (:n, 'Personel', 'AKTİF', 6, :d, :y)
                """), {"n": real_name, "d": d_id, "y": s_id})
                conn.commit()
                count += 1
                
        print(f"\n✅ Toplam {count} yeni personel eklendi.")

except Exception as e:
    print(f"❌ Error: {e}")
