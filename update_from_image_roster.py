
import pandas as pd
from sqlalchemy import create_engine, text

# 1. RAW DATA FROM IMAGE
# Format: (Ad Soyad, Bolum, Bolum Sorumlusu)
raw_data = [
    ("ABDULRAOUF O A BARGHOUTH", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("ABDULDAYIM ABDURREZZAK", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ABDULHADİ KURTAY", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDULLAH ALHANZAL", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("ABDULRAHİM EİD", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDULRAHMAN KALLAS", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDURRAHMAN SUKKAR", "PATAŞU", "NURETTİN SOLAKLI"),
    ("ABDURRAHMAN ARAB", "DOMBA", "YELİZ ÇAKIR"), # DOMBA -> BOMBA
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
    ("FATMA GÜLŞEN", "BOMBA", "YELİZ ÇAKIR"), # Image says FATMA GÜLŞEN
    ("GURBET  KIYAR", "BOMBA", "YELİZ ÇAKIR"),
    ("GÜLAY  MUTLU", "BOMBA", "YELİZ ÇAKIR"),
    ("GÜLER DEMİRDEN", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("GÜLŞEN NİCE", "RULO PASTA", "MİHRİBAN ALİ"),
    ("HAMİYET  UYMAZ", "BOMBA", "YELİZ ÇAKIR"),
    ("HAMZA ASHRAM", "DOMBA", "YELİZ ÇAKIR"), # DOMBA
    ("HASAN  YILMAZ", "PATAŞU", "NURETTİN SOLAKLI"),
    ("HASSAN HABRA", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("HASSAN HABRA", "PANDİSPANYA", "CEMAL İSMAİL"), # Duplicate in image?
    ("HAŞEM   ARİF", "PROFİTEROL", "BATIKAN ARSLAN"),
    ("HAYSAM KORANİ", "PANDİSPANYA", "CEMAL İSMAİL"),
    ("HOSSAM ALDIN  ALTAHAN", "HALKA TATLI", "ERKAN DEMİR"),
    ("HSAN KAFRNAAR", "PATAŞU", "NURETTİN SOLAKLI"),
    ("HUSSAMALDEEN BAZARBASHI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İBRAHİM KARANDI", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İBRAHİM KERİMOĞLU", "PATAŞU", "NURETTİN SOLAKLI"),
    ("İSMAİL ÖMEROĞLU", "HALKA TATLI", "ERKAN DEMİR"), # Image says HALKA TATLI
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
    ("NESRİN ADA", "DOMBA", "YELİZ ÇAKIR"), # DOMBA
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
    ("TELAL ŞAKİFA", "BOMBA", "YELİZ ÇAKIR"), # DOMBA/BOMBA? Image says BOMBA
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

# 2. HELPER FUNCTIONS
def get_clean_name(name):
    # Standardize spaces and uppercase
    return str(name).replace('  ', ' ').strip().upper()

def run_update():
    engine = create_engine('sqlite:///ekleristan_local.db')
    
    print("Personel atamalari gorsel veri tabanindan yukleniyor...")
    
    with engine.begin() as conn:
        # Load Existing Departments
        depts_df = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", conn)
        # Create map: "PROFİTEROL" -> ID
        dept_map = {}
        for _, row in depts_df.iterrows():
            d_name = get_clean_name(row['bolum_adi'])
            dept_map[d_name] = row['id']
            # Special manual mappings for variations
            if d_name == "PANDİSPANYA": dept_map["KEK"] = row['id'] 
            if d_name == "BOMBA": dept_map["DOMBA"] = row['id']
            
        print(f" {len(dept_map)} departman haritalandi.")
        
        # Load Supervisor Names -> IDs
        # We need ALL personnel because supervisors are also personnel
        pers_df = pd.read_sql("SELECT id, ad_soyad FROM personel", conn)
        name_to_id = {}
        for _, row in pers_df.iterrows():
            clean_n = get_clean_name(row['ad_soyad'])
            name_to_id[clean_n] = row['id']
            
        print(f" {len(name_to_id)} mevcut personel sistemde bulundu.")
        
        # 3. Process Logic
        updated_count = 0
        not_found_count = 0
        
        for name, dept_name, sup_name in raw_data:
            clean_p_name = get_clean_name(name)
            clean_d_name = get_clean_name(dept_name)
            clean_s_name = get_clean_name(sup_name)
            
            # Map Department
            d_id = dept_map.get(clean_d_name)
            if not d_id and clean_d_name == "DOMBA": d_id = dept_map.get("BOMBA")
            
            # Map Supervisor
            s_id = name_to_id.get(clean_s_name)
            
            # Find Person ID
            p_id = name_to_id.get(clean_p_name)
            
            if p_id:
                # Update
                # Only update if we found valid dept/supervisor
                update_parts = []
                params = {"pid": p_id}
                
                if d_id:
                    update_parts.append("departman_id = :did, bolum = :dname")
                    params["did"] = d_id
                    params["dname"] = dept_name # Keep original text in bolum
                
                if s_id:
                    update_parts.append("yonetici_id = :sid")
                    params["sid"] = s_id
                    
                if update_parts:
                     sql = f"UPDATE personel SET {', '.join(update_parts)} WHERE id = :pid"
                     conn.execute(text(sql), params)
                     updated_count += 1
            else:
                # print(f" Bulunamadi: {clean_p_name}")
                not_found_count += 1
                
        print(f" Otomatik Atama Tamamlandi!")
        print(f" {updated_count} personel guncellendi.")
        print(f" {not_found_count} personel sistemde bulunamadi (Isim eslesmedi).")

if __name__ == "__main__":
    run_update()
