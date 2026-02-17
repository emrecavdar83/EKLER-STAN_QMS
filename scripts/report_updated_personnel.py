import sqlite3
import pandas as pd

def report_updates():
    conn = sqlite3.connect('ekleristan_local.db')
    
    print("--- Departman Bilgisi Güncellenen Personeller ---")
    
    # 1. Güncellenenler (departman_id > 0)
    query_updated = """
    SELECT p.id, p.ad_soyad, p.bolum, b.bolum_adi as atanan_departman
    FROM personnel p
    LEFT JOIN ayarlar_bolumler b ON p.departman_id = b.id
    WHERE p.departman_id > 0
    ORDER BY p.ad_soyad
    """
    df_updated = pd.read_sql(query_updated, conn)
    
    print(f"\n[OK] TOPLAM GUNCELLENEN: {len(df_updated)} Kisi\n")
    print(df_updated.to_string(index=False))
    
    # 2. Güncellenmeyenler (departman_id = 0)
    query_not_updated = """
    SELECT id, ad_soyad, bolum
    FROM personnel
    WHERE departman_id = 0
    ORDER BY ad_soyad
    """
    df_not_updated = pd.read_sql(query_not_updated, conn)
    
    print(f"\n\n[!] GUNCELLENMEYEN / ISTISNA (Eslesmeyen): {len(df_not_updated)} Kisi\n")
    if not df_not_updated.empty:
        print(df_not_updated.to_string(index=False))
        
    conn.close()

if __name__ == "__main__":
    report_updates()
