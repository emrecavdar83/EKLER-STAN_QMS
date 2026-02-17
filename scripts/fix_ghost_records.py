import sqlite3
import pandas as pd
import os
import sys

# Türkçe karakter desteği için
sys.stdout.reconfigure(encoding='utf-8')

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
    return " ".join(name.split())

def main():
    print("=== PERSONEL VERİ TEMİZLİĞİ VE EŞİTLEME ===")
    
    db_path = 'ekleristan_local.db'
    txt_path = 'personnel_update_20260131.txt'
    
    if not os.path.exists(txt_path):
        print(f"HATA: '{txt_path}' dosyası bulunamadı!")
        return

    try:
        # 1. Veritabanı Bağlantısı ve Mevcut Veriyi Çekme
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQL Injection ve Syntax hatasına karşı parametreli sorgu örneği (okuma için gerekmez ama alışkanlık olsun)
        cursor.execute("SELECT id, ad_soyad FROM personnel")
        db_rows = cursor.fetchall()
        print(f"Veritabanındaki toplam kayıt sayısı: {len(db_rows)}")
        
        # 2. Referans Listeyi Okuma
        try:
            df = pd.read_csv(txt_path, sep='\t', encoding='utf-8')
        except UnicodeDecodeError:
             df = pd.read_csv(txt_path, sep='\t', encoding='cp1254')
             
        # İkinci sütun isim varsayımı (Adı Soyadı)
        name_col = df.columns[1]
        file_names = df[name_col].apply(normalize_name).tolist()
        target_names_set = set(file_names)
        
        print(f"Listede bulunan kişi sayısı: {len(file_names)}")
        
        # 3. Fark Analizi
        extras = []
        ids_to_delete = []
        
        for pid, name in db_rows:
            norm_name = normalize_name(name)
            if norm_name not in target_names_set:
                extras.append((pid, name))
                ids_to_delete.append(pid)
        
        # 4. Silme İşlemi
        if not extras:
            print("\nTEBRİKLER: Veritabanı ile liste tam uyumlu. Fark yok.")
        else:
            print(f"\nVeritabanında olup listede OLMAYAN {len(extras)} kişi tespit edildi:")
            print("-" * 50)
            for pid, name in extras:
                print(f"ID: {pid} - {name} [SİLİNECEK]")
            print("-" * 50)
            
            # Toplu silme işlemi (Parametreli sorgu ile güvenli silme)
            # "DELETE FROM personnel WHERE id IN (?, ?, ...)"
            if ids_to_delete:
                placeholders = ', '.join(['?'] * len(ids_to_delete))
                sql = f"DELETE FROM personnel WHERE id IN ({placeholders})"
                cursor.execute(sql, ids_to_delete)
                conn.commit()
                print(f"\nBAŞARILI: {cursor.rowcount} adet kayıt veritabanından silindi.")
            
        # 5. Son Kontrol
        cursor.execute("SELECT COUNT(*) FROM personnel")
        final_count = cursor.fetchone()[0]
        print(f"\nSon Durum - Veritabanı Personel Sayısı: {final_count}")
        
        if final_count == 184:
            print("SONUÇ: HEDEF TUTTURULDU (184 Kişi).")
        else:
            print(f"UYARI: Hedef 184 idi, şuan {final_count}. Lütfen kontrol edin.")

        conn.close()

    except Exception as e:
        print(f"BEKLENMEDİK HATA: {e}")

if __name__ == "__main__":
    main()
