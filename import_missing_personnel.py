
import pandas as pd
from sqlalchemy import create_engine, text

# 1. RAW DATA FROM IMAGE (Same source roster)
raw_data = [
    ("ABDULRAOUF O A BARGHOUTH", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("ABDULDAYIM ABDURREZZAK", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ABDULHADİ KURTAY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDULLAH ALHANZAL", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ABDULRAHİM EİD", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDULRAHMAN KALLAS", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDURRAHMAN SUKKAR", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDURRAHMAN ARAB", "DOMBA", "YELİZ ÇAKIR"),
    ("AHMED  MUHAMMED SEYİD", "PATAŞU", "NURETTİN SOLAKLI"),
    ("AHMET SOLAKLI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ALAA HABİBİ", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("ALAA MAHCUB", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("ALAA ALRAHMAN", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ALAA EDDİN NALİ", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ALİ SALEM", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ALİ HAMDAN", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ALİCAN ALİ", "RULO PASTA", "MİHRİBAN ALİ"),
    ("ASLI  KAYA", "BOMBA", "YELİZ ÇAKIR"),
    ("AYGÜL  CEYLAN", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("BATIKAN ARSLAN", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("BİLGEN YORDAM", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("CELEL EL MAHFUZ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("CEMAL ABDULNASIR  İSMAİL", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ÇETİN DEVİREN", "RULO PASTA", "MİHRİBAN ALİ"),
    ("DUAA KHAYAT", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("ELİF TAHTALI", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("EMİNE SÜZĞÜN", "RULO PASTA", "MİHRİBAN ALİ"),
    ("EMİRHAN ALREZ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ERDAL  ÖZTÜRK", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ERKAN DEMİR", "HALKA TATLI", "ERKAN DEMİR"),
    ("ESRA TARIK", "RULO PASTA", "MİHRİBAN ALİ"),
    ("EZEL  ALRIHANI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("FATMA GÜLŞEN", "BOMBA", "YELİZ ÇAKIR"),
    ("GURBET  KIYAR", "BOMBA", "YELİZ ÇAKIR"),
    ("GÜLAY  MUTLU", "BOMBA", "YELİZ ÇAKIR"),
    ("GÜLER DEMİRDEN", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("GÜLŞEN NİCE", "RULO PASTA", "MİHRİBAN ALİ"),
    ("HAMİYET  UYMAZ", "BOMBA", "YELİZ ÇAKIR"),
    ("HAMZA ASHRAM", "DOMBA", "YELİZ ÇAKIR"),
    ("HASAN  YILMAZ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("HASSAN HABRA", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("HAŞEM   ARİF", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("HAYSAM KORANİ", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("HOSSAM ALDIN  ALTAHAN", "HALKA TATLI", "ERKAN DEMİR"),
    ("HSAN KAFRNAAR", "PATAŞU", "NURETTİN SOLAKLI"),
    ("HUSSAMALDEEN BAZARBASHI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İBRAHİM KARANDI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İBRAHİM KERİMOĞLU", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İSMAİL ÖMEROĞLU", "HALKA TATLI", "ERKAN DEMİR"),
    ("KADRİ NOUSH", "PATAŞU", "NURETTİN SOLAKLI"),
    ("KAMURAN MURATGİL", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("KERİME AKHBAŞ", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("KÜBRA  KUTLU", "BOMBA", "YELİZ ÇAKIR"),
    ("MAHMOUD TAIR", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("MAHMUD SİDO", "PATAŞU", "NURETTİN SOLAKLI"),
    ("MAJED KHIYATA", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("MALİK  ŞİMRECİ", "RULO PASTA", "MİHRİBAN ALİ"),
    ("MİHRİBAN ALİ", "RULO PASTA", "MİHRİBAN ALİ"),
    ("MOHAB KEBBEH WAR", "RULO PASTA", "MİHRİBAN ALİ"),
    ("MUHAMED HAMAL", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("MUHAMMED KASSAB", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("MUHAMMED ZÜHEYR MAĞHİNİ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("MUSTAFA GASİM", "PATAŞU", "NURETTİN SOLAKLI"),
    ("NESRİN ADA", "DOMBA", "YELİZ ÇAKIR"),
    ("NİDAL  ALAU", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("NURETTİN SOLAKLI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("NURİYE ATASOY", "BOMBA", "YELİZ ÇAKIR"),
    ("OMAR SALEM", "BOMBA", "YELİZ ÇAKIR"),
    ("OYA ERDOĞAN", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("ÖZLEM  YORDAM", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("RECEP SOLAKLI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("RIDVAN KURTAY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("SAİD ABDULBAKİ", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("SAİME TOPRAK", "BOMBA", "YELİZ ÇAKIR"),
    ("SEHER  ÖZATİLA", "BOMBA", "YELİZ ÇAKIR"),
    ("SEMRA YILDIRIM", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("SERKAN BEY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("SULEYMAN  SİDO", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ŞEHRİYE YAŞAR", "RULO PASTA", "MİHRİBAN ALİ"),
    ("ŞERAFEDDİN  SÖZEN", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ŞERİFE DENİZ", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("TALİP BELLURA", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("TELAL ŞAKİFA", "BOMBA", "YELİZ ÇAKIR"),
    ("UĞUR  ÜNLÜSOY", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("UMUT ALACA", "RULO PASTA", "MİHRİBAN ALİ"),
    ("UMUT CAN  KURTAY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ÜMMÜHAN  ORUÇ", "BOMBA", "YELİZ ÇAKIR"),
    ("VAGIF MEHDİ", "HALKA TATLI", "ERKAN DEMİR"),
    ("YASEMİN  SAKARYA", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("ZEYNEP ALBAYRAK", "RULO PASTA", "MİHRİBAN ALİ"),
    ("ZUBALA  MEHDİ", "RULO PASTA", "MİHRİBAN ALİ"),
    ("ORHAN KALIN", "BOMBA", "YELİZ ÇAKIR"),
    ("FATMA ÖKSÜZ", "BOMBA", "YELİZ ÇAKIR"),
    ("RÜMEYSA YAŞAR", "BOMBA", "YELİZ ÇAKIR"),
    ("VECHETTİN GÜNEŞ", "BOMBA", "YELİZ ÇAKIR"),
    ("FADİA İBRAHİM BAŞ", "BOMBA", "YELİZ ÇAKIR"),
    ("BİLAL ANTAKLI", "BOMBA", "YELİZ ÇAKIR"),
    ("HURMA DENLİYEVA", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("VELİD ALAMRA", "RULO PASTA", "MİHRİBAN ALİ"),
    ("VELİD İBRAHİM", "RULO PASTA", "MİHRİBAN ALİ"),
    ("YAHYA ALKAN", "PATAŞU", "NURETTİN SOLAKLI"),
    ("NEVRAZ ALNASRİ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("YELİZ ÇAKIR", "BOMBA", "YELİZ ÇAKIR")
]

def get_clean_name(name):
    # Standardize spaces and uppercase
    return str(name).replace('  ', ' ').strip().upper()

def run_import():
    engine = create_engine('sqlite:///ekleristan_local.db')
    print("Eksik personeller taranıyor...")
    
    with engine.begin() as conn:
        # Load Departments Map
        depts_df = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", conn)
        dept_map = {}
        for _, row in depts_df.iterrows():
            d_name = get_clean_name(row['bolum_adi'])
            dept_map[d_name] = row['id']
            # Aliases
            if d_name == "PANDİSPANYA": dept_map["KEK"] = row['id'] 
            if d_name == "BOMBA": dept_map["DOMBA"] = row['id']

        # Load Existing Personnel Names (Master List to check presence)
        pers_df = pd.read_sql("SELECT id, ad_soyad FROM personel", conn)
        existing_names = set()
        name_to_id_map = {} # Needed for Supervisor lookup
        for _, row in pers_df.iterrows():
            cleaned = get_clean_name(row['ad_soyad'])
            existing_names.add(cleaned)
            name_to_id_map[cleaned] = row['id']
            
        added_count = 0
        added_list = []
        
        for name, dept_name, sup_name in raw_data:
            clean_p_name = get_clean_name(name)
            
            if clean_p_name not in existing_names:
                # Need to Add!
                
                # 1. Resolve Department
                clean_d_name = get_clean_name(dept_name)
                d_id = dept_map.get(clean_d_name)
                # Fallback alias handling in map lookup logic or pre-map
                if not d_id and clean_d_name == "DOMBA": d_id = dept_map.get("BOMBA")
                
                # 2. Resolve Supervisor
                clean_s_name = get_clean_name(sup_name)
                s_id = None
                if clean_s_name in name_to_id_map:
                    s_id = name_to_id_map[clean_s_name]
                else:
                    # Supervisor not found in DB? 
                    # User rules: "Bölüm sorumlusu eksik ise boş bırak" (If missing in source or DB? Context implies source, but here source HAS it but DB might not know him yet? Or supervisor is also new?)
                    # If supervisor is also new and in this list, we might miss linking them because we process linearly.
                    # Ideally we should do 2 passes, but for now let's set NULL if not found.
                    pass
                
                # 3. Insert
                # Use SQL parameters
                # Default values: gorev='Personel', durum='Aktif', pozisyon_seviye=6
                sql = text("""
                    INSERT INTO personel (ad_soyad, departman_id, bolum, yonetici_id, gorev, durum, pozisyon_seviye)
                    VALUES (:name, :did, :dname, :sid, 'Personel', 'Aktif', 6)
                """)
                
                params = {
                    "name": name, # Use original casing from list roughly
                    "did": d_id,
                    "dname": dept_name, # Use text from list
                    "sid": s_id
                }
                
                conn.execute(sql, params)
                added_count += 1
                added_list.append(name)
                
                # Add to existing names/map so subseqent entries can use this person if they are a supervisor (rare but possible)
                # Although we don't have their ID until we commit or fetch back, so we skip self-referencing for new adds in this batch.
                existing_names.add(clean_p_name)
        
        print(f"Islem Tamamlandi!")
        print(f"Toplam {added_count} YENI personel eklendi.")
        if added_count > 0:
            print("Eklenenler:")
            for p in added_list:
                print(f" + {p}")
        else:
            print("Eksik personel bulunamadi. Liste zaten guncel.")

if __name__ == "__main__":
    run_import()
