import sqlite3
import pandas as pd

def apply_migration():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    print("1. Updating Schema...")
    # Add BAKIM/TEKNİK under ÜRETİM (ID=2)
    cursor.execute("INSERT INTO qms_departmanlar (ad, tur_id, ust_id, sira_no, aktif) VALUES ('BAKIM/TEKNİK', 2, 2, 50, 1)")
    bakim_id = cursor.lastrowid
    
    # Add HALKA TATLI under HACI NADİR (ID=10)
    cursor.execute("INSERT INTO qms_departmanlar (ad, tur_id, ust_id, sira_no, aktif) VALUES ('HALKA TATLI', 2, 10, 50, 1)")
    halka_id = cursor.lastrowid
    
    print("2. Cleaning up Personnel...")
    cursor.execute("DELETE FROM personel WHERE ad_soyad LIKE '%SEFER CAN ER%'")
    
    print("3. Fetching Data for Mapping...")
    new_depts = pd.read_sql("SELECT id, ad FROM qms_departmanlar", conn)
    
    def get_id(name):
        res = new_depts[new_depts['ad'].str.upper() == name.upper()]
        return int(res.iloc[0]['id']) if not res.empty else None

    # Hardcoded/Specific Mappings from User Feedback
    specific_mapping = {
        "BAKIM": bakim_id,
        "HALKA TATLI": halka_id,
        "YÖNETİM": get_id("GENEL MÜDÜRLÜK"),
        "DEPO": get_id("MAMÜL DEPO"),
        "GENEL TEMİZLİK": get_id("TEMİZLİK"),
        "ET İŞLEME": get_id("ÜRETİM"),
        "HAMMADDE DEPO": get_id("HAM MADDE DEPO")
    }
    
    # Get all personnel
    pers_df = pd.read_sql("SELECT id, ad_soyad, bolum FROM personel WHERE qms_departman_id IS NULL", conn)
    
    count = 0
    for _, row in pers_df.iterrows():
        old_name = str(row['bolum']).strip()
        target_id = None
        
        # Rule 1: Specific Mapping
        if old_name in specific_mapping:
            target_id = specific_mapping[old_name]
        
        # Rule 2: Strip "Ekler " prefix and check
        if not target_id and old_name.startswith("Ekler "):
            clean_name = old_name.replace("Ekler ", "").split(" - ")[0].strip()
            # Map specific clean names
            if "Krema" in clean_name: clean_name = "KREMA"
            if "Paket" in clean_name: clean_name = "SEVKİYAT"
            if "Bulaşkhane" in clean_name: clean_name = "BULAŞIKHANE"
            if "Temizlik" in clean_name: clean_name = "TEMİZLİK"
            if "Magnolia" in clean_name: clean_name = "MAGNOLYA"
            if "Meyve" in clean_name: clean_name = "MEYVE"
            if "Dolumu" in clean_name or "Dolum" in clean_name: clean_name = "DOLUM"
            if "Dam" in clean_name: clean_name = "ÜRETİM" # Fallback for Dam
            if "Makaron" in clean_name: clean_name = "KURU PASTA"
            
            target_id = get_id(clean_name)
            
            # Rule 4: If still not found, try mapping by keyword
            if not target_id:
                if "Asansör" in clean_name or "Meydancı" in clean_name or "Palet" in clean_name:
                    target_id = get_id("SEVKİYAT")
                elif "Kasa" in clean_name or "Tepsi" in clean_name:
                    target_id = get_id("TEMİZLİK")
            
        if target_id:
            cursor.execute("UPDATE personel SET qms_departman_id = ? WHERE id = ?", (target_id, row['id']))
            count += 1
            
    conn.commit()
    print(f"4. Migration Complete! {count} personals updated.")
    conn.close()

if __name__ == "__main__":
    apply_migration()
