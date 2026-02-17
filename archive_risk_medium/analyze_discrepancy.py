
import sqlite3
import pandas as pd
import sys

def normalize_name(name):
    if not isinstance(name, str): return ""
    # Turkish character mapping
    replacements = {
        'İ': 'I', 'ı': 'I',
        'Ö': 'O', 'ö': 'O',
        'Ü': 'U', 'ü': 'U',
        'Ş': 'S', 'ş': 'S',
        'Ğ': 'G', 'ğ': 'G',
        'Ç': 'C', 'ç': 'C',
    }
    name = name.upper()
    for k, v in replacements.items():
        name = name.replace(k, v)
    return " ".join(name.split()) # Remove extra whitespace

def analyze():
    try:
        # Read DB
        conn = sqlite3.connect('ekleristan_local.db')
        db_df = pd.read_sql("SELECT id, ad_soyad FROM personnel", conn)
        conn.close()
        
        # Read file - try different encodings for robustness
        file_path = 'personnel_update_20260131.txt'
        try:
            file_df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        except:
            try:
                 file_df = pd.read_csv(file_path, sep='\t', encoding='cp1254')
            except:
                 file_df = pd.read_csv(file_path, sep='\t', encoding='latin1')
        
        # Identify name column (likely 2nd column if headers are problematic)
        # Based on preview: Sno, Adı Soyadı, ...
        name_col = file_df.columns[1] 
        print(f"Using column '{name_col}' for names from text file.")

        target_names = set(file_df[name_col].apply(normalize_name))
        
        print(f"\nDB Total Records: {len(db_df)}")
        print(f"Target List Records: {len(file_df)}")
        print(f"Unique Target Names: {len(target_names)}")
        
        ids_to_delete = []
        extras = []
        
        for idx, row in db_df.iterrows():
            norm_name = normalize_name(row['ad_soyad'])
            if norm_name not in target_names:
                extras.append((row['id'], row['ad_soyad']))
                ids_to_delete.append(row['id'])
        
        if not extras:
            print("\nSUCCESS: No discrepancies found. DB matches the list.")
        else:
            print(f"\nFound {len(extras)} extra records in DB that are NOT in the target list:")
            print("-" * 60)
            print(f"{'ID':<5} | {'Name'}")
            print("-" * 60)
            for pid, name in extras:
                print(f"{pid:<5} | {name}")
            print("-" * 60)
            
            # Suggest deletions
            print("\nTo delete these records, the IDs are:")
            print(ids_to_delete)

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze()
