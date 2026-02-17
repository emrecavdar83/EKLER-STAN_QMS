import sqlite3
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

def inspect_relations():
    conn = sqlite3.connect('ekleristan_local.db')
    

    
    print("\n--- Personel Tablosu Örneği ---")
    # Check available columns first
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(personnel)")
    cols = [info[1] for info in cursor.fetchall()]
    
    target_cols = ["id", "ad_soyad", "bolum", "departman_id", "yonetici_id"]
    query_cols = [c for c in target_cols if c in cols]
    
    missing_cols = set(target_cols) - set(cols)
    if missing_cols:
        print(f"UYARI: 'personnel' tablosunda eksik sütunlar var: {missing_cols}")
    
    query = f"SELECT {', '.join(query_cols)} FROM personnel LIMIT 10"
    df_p = pd.read_sql(query, conn)
    print(df_p.to_string())
    
    print("\n\n--- Departmanlar Tablosu (Ayarlar_Bolumler) ---")
    try:
        df_d = pd.read_sql("SELECT * FROM ayarlar_bolumler", conn)
        print(df_d.to_string())
        
        # Simple analysis of relation
        if 'bolum' in df_p.columns and not df_d.empty:
             print("\n--- Analiz: Personel 'bolum' değerleri ve 'ayarlar_bolumler' karşılaştrıması ---")
             # Assuming 'bolum' in personnel might match 'bolum_adi' or 'id' in ayarlar_bolumler
             unique_personnel_bolum = df_p['bolum'].unique()
             print(f"Personeldeki benzersiz 'bolum' değerleri (ilk 10): {unique_personnel_bolum}")
             
    except Exception as e:
        print(f"'ayarlar_bolumler' tablosu sorunu: {e}")
        
    conn.close()

if __name__ == "__main__":
    inspect_relations()
