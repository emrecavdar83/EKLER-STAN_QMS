import sqlite3
import pandas as pd
import sys

# Türkçe karakter desteği
sys.stdout.reconfigure(encoding='utf-8')

def report_missing():
    try:
        conn = sqlite3.connect('ekleristan_local.db')
        
        # Sütunları tekrar kontrol edelim
        # id, ad_soyad, bolum, gorev, vardiya, durum, servis_duragi, telefon_no
        
        # Boş string veya NULL kontrolü
        query = """
        SELECT id, ad_soyad, bolum, gorev
        FROM personnel 
        WHERE (bolum IS NULL OR bolum = '' OR bolum = 'None')
           OR (gorev IS NULL OR gorev = '' OR gorev = 'None')
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print("=== EKSİK BİLGİ RAPORU ===")
        print(f"Tarama Zamanı: {pd.Timestamp.now()}\n")
        
        if df.empty:
            print("TEBRİKLER: Bölüm veya Sorumlu (Görev) bilgisi boş olan personel bulunmamaktadır.")
        else:
            print(f"TOPLAM {len(df)} ADET EKSİK KAYIT BULUNDU:")
            print("-" * 60)
            print(f"{'ID':<5} | {'AD SOYAD':<25} | {'BÖLÜM (DEPT)':<15} | {'SORUMLU/GÖREV'}")
            print("-" * 60)
            
            for _, row in df.iterrows():
                dept = row['bolum'] if row['bolum'] else "--- BOŞ ---"
                role = row['gorev'] if row['gorev'] else "--- BOŞ ---"
                print(f"{row['id']:<5} | {row['ad_soyad']:<25} | {dept:<15} | {role}")
            
            print("-" * 60)
            print("\nNOT: 'Sorumlu' sütunu veritabanında 'gorev' (Role/Duty) olarak aranmıştır.")
            
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    report_missing()
