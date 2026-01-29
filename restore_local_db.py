import pandas as pd
import sqlite3
import os

def restore_local():
    db_path = 'ekleristan_local.db'
    data_dir = 'data_sync'
    
    if not os.path.exists(data_dir):
        print(f"HATA: {data_dir} klasörü bulunamadı!")
        return

    conn = sqlite3.connect(db_path)
    
    print(f"--- {db_path} Veri Geri Yükleme Başlatıldı ---")

    # Klasördeki tüm CSV'leri oku
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    print(f"Toplam {len(csv_files)} CSV dosyası bulundu.")

    for file in csv_files:
        tablo_adi = file.replace('.csv', '')
        csv_path = os.path.join(data_dir, file)
        
        try:
            print(f"-> {tablo_adi} geri yükleniyor...")
            df = pd.read_csv(csv_path)
            
            if df.empty:
                print(f"   UYARI: {tablo_adi} dosyası boş.")
                continue

            # Veritabanındaki kolonları al
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({tablo_adi})")
            db_cols = [col[1] for col in cursor.fetchall()]
            
            if not db_cols:
                # Tablo yoksa CSV kolonlarıyla oluştur
                print(f"   BILGI: {tablo_adi} tablosu oluşturuluyor...")
                df.to_sql(tablo_adi, conn, if_exists='replace', index=False)
            else:
                # Sadece hem CSV'de hem DB'de olan kolonları seç
                csv_cols = df.columns.tolist()
                common_cols = [c for c in csv_cols if c in db_cols]
                
                missing_in_csv = [c for c in db_cols if c not in csv_cols and c != 'id']
                if missing_in_csv:
                    print(f"   UYARI: DB'deki şu kolonlar CSV'de yok: {missing_in_csv}")
                
                # Tabloyu temizle ve sadece ortak kolonları yükle
                cursor.execute(f"DELETE FROM {tablo_adi}")
                conn.commit()
                df[common_cols].to_sql(tablo_adi, conn, if_exists='append', index=False)
            
            print(f"   OK: {len(df)} kayıt işlendi.")
        except Exception as e:
            print(f"   HATA: {tablo_adi} yüklenemedi: {e}")

    conn.close()
    print("--- Veri Geri Yükleme Tamamlandı ---")

if __name__ == "__main__":
    restore_local()
