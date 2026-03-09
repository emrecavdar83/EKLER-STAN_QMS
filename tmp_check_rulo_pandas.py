import sqlite3
import pandas as pd

def check_personnel_sqlite():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    
    with open('tmp_rulo_analyze.txt', 'w', encoding='utf-8') as f:
        query = """
        SELECT p.ad_soyad, d.bolum_adi as bolum, p.vardiya, p.durum 
        FROM personel p 
        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id 
        WHERE p.ad_soyad IS NOT NULL
        """
        p_list = pd.read_sql_query(query, conn)
        
        f.write(f"Org p_list size: {len(p_list)}\n")
        
        p_list['durum_raw'] = p_list['durum']
        p_list['durum'] = p_list['durum'].astype(str).str.strip().str.upper()
        p_list['vardiya_raw'] = p_list['vardiya']
        p_list['vardiya'] = p_list['vardiya'].astype(str).str.strip()
        p_list['bolum_raw'] = p_list['bolum']
        p_list['bolum'] = p_list['bolum'].astype(str).str.strip()
        
        active_list = p_list[p_list['durum'] == "AKTİF"]
        
        f.write(f"Active p_list size: {len(active_list)}\n")
        
        rulo = active_list[active_list['bolum'].str.contains('Rulo', case=False, na=False)]
        
        f.write(f"Rulo Active count: {len(rulo)}\n")
        for idx, row in rulo.iterrows():
            f.write(f"Ad: '{row['ad_soyad']}', Vardiya: '{row['vardiya']}' (raw: '{row['vardiya_raw']}'), Bolum: '{row['bolum']}' (raw: '{row['bolum_raw']}'), Durum_raw: '{row['durum_raw']}'\n")

if __name__ == "__main__":
    check_personnel_sqlite()
