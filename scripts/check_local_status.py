import sqlite3
import pandas as pd

def check_status():
    print("--- Lokal Veritabanı (ekleristan_local.db) Durumu ---")
    try:
        conn = sqlite3.connect('ekleristan_local.db')
        cursor = conn.cursor()
        
        # 1. Tablo yapısını kontrol et
        cursor.execute("PRAGMA table_info(personnel)")
        cols = [info[1] for info in cursor.fetchall()]
        print(f"Mevcut Sütunlar: {cols}")
        
        if 'departman_id' in cols and 'yonetici_id' in cols:
            print("\n[OK] Sema guncellemeleri (departman_id, yonetici_id) MEVCUT.")
        else:
            print("\n[HATA] Sema guncellemeleri EKSIK.")
            
        # 2. Veri doluluk oranını kontrol et
        total = pd.read_sql("SELECT count(*) as cnt FROM personnel", conn).iloc[0]['cnt']
        mapped = pd.read_sql("SELECT count(*) as cnt FROM personnel WHERE departman_id > 0", conn).iloc[0]['cnt']
        
        print(f"\nToplam Personel Sayısı: {total}")
        print(f"Departmanı Eşleşen Personel Sayısı: {mapped}")
        print(f"Eşleşme Oranı: %{mapped/total*100:.1f}")
        
        # 3. Örnek Veriler
        print("\n--- Örnek Kayıtlar (İlk 5) ---")
        df_sample = pd.read_sql("SELECT id, ad_soyad, bolum, departman_id FROM personnel WHERE departman_id > 0 LIMIT 5", conn)
        print(df_sample.to_string(index=False))
        
        print("\n--- Eşleşmeyenlerden Örnekler (Varsa) ---")
        df_unmapped = pd.read_sql("SELECT id, ad_soyad, bolum, departman_id FROM personnel WHERE departman_id = 0 LIMIT 5", conn)
        if not df_unmapped.empty:
            print(df_unmapped.to_string(index=False))
        else:
            print("Tüm kayıtlar eşleşti veya eşleşmeyen yok.")

        conn.close()
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    check_status()
