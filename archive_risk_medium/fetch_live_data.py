import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- 1. AYARLAR ---
# Bu script için manuel DB_URL gerekebilir çünkü secrets.toml lokalde boş.
# Kullanıcıdan veya ortam değişkeninden alınabilir.
# Güvenlik nedeniyle buraya yazmıyorum, kullanıcıdan script çalıştığında soracağım.

def fetch_data(provided_url=None):
    if provided_url:
        db_url = provided_url
    else:
        db_url = input("Lütfen Supabase DB_URL adresini giriniz: ").strip()
    if not db_url:
        print("HATA: DB_URL boş olamaz!")
        return

    try:
        engine = create_engine(db_url)
        print("Canlı veritabanına bağlanıldı...")
        
        # CSV'lerin kaydedileceği klasör
        os.makedirs("data_sync", exist_ok=True)

        # Dinamik Tablo ve View Listesi Keşfi
        with engine.connect() as conn:
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type IN ('BASE TABLE', 'VIEW')
            """)
            result = conn.execute(query)
            tablolar = [row[0] for row in result]
            
        print(f"Keşfedilen toplam tablo/view sayısı: {len(tablolar)}")

        for tablo in tablolar:
            try:
                print(f"-> {tablo} verisi çekiliyor...")
                df = pd.read_sql(f'SELECT * FROM "{tablo}"', engine)
                
                # Dosyaya kaydet
                df.to_csv(f"data_sync/{tablo}.csv", index=False)
                print(f"   OK: {len(df)} kayıt kaydedildi.")
            except Exception as e:
                print(f"   UYARI: {tablo} çekilemedi: {e}")

        print("\n--- Veri Çekme İşlemi Tamamlandı (./data_sync klasöründe) ---")

    except Exception as e:
        print(f"Bağlantı Hatası: {e}")

if __name__ == "__main__":
    fetch_data()
