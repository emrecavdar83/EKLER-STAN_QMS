import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
import toml
from datetime import datetime

# ANAYASA MADDE 7: Cloud-Primary Mimari (Offline Read-Only Yedek Modülü)
# Bu script günde 1 kez (Örn: CRON veya Windows Task Scheduler) çalıştırılmalıdır.
# Supabase üzerindeki "Single Source of Truth" verilerini alır ve 
# lokalde sadece "Okuma Amaçlı" bir ekleristan_offline_backup.db dosyasına basar.
# Streamlit arayüzü internet koptuğunda bu dosyayı okuyacaktır.

def get_live_url():
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets.get("streamlit", {}).get("DB_URL") or secrets.get("DB_URL")
        # Remove quotes if any
        if url and url.startswith('"') and url.endswith('"'):
            url = url[1:-1]
        return url
    except Exception as e:
        print(f"Hata: .streamlit/secrets.toml okunamadi ({e})")
        return None

def run_backup():
    print(f"--- offline_yedek_basladi: {datetime.now()} ---")
    live_url = get_live_url()
    
    if not live_url:
        print("HATA: Supabase bağlantı dizesi (DB_URL) bulunamadığından yedek alınamıyor.")
        return

    print("☁️ Supabase Cloud'a bağlanılıyor...")
    live_engine = create_engine(live_url, connect_args={"connect_timeout": 10})
    
    local_db_path = 'ekleristan_offline_backup.db'
    temp_db_path = 'ekleristan_offline_temp.db'
    
    # Güvenli yedekleme: Önce temp dosyaya yaz, başarılıysa eskisinin üstüne yaz
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
    
    local_conn = sqlite3.connect(temp_db_path)
    
    kopyalanan_tablo_sayisi = 0
    toplam_kayit = 0

    try:
        with live_engine.connect() as conn:
            # Public şema altındaki tüm tabloları çek
            query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = conn.execute(query).fetchall()
            
            for t in tables:
                table_name = t[0]
                try:
                    df = pd.read_sql(f"SELECT * FROM \"{table_name}\"", conn)
                    # NaN ve benzeri değerleri SQLite için düzelt
                    df.to_sql(table_name, local_conn, if_exists='replace', index=False)
                    kopyalanan_tablo_sayisi += 1
                    toplam_kayit += len(df)
                    print(f"✅ {table_name}: {len(df)} kayıt yedeğe alındı.")
                except Exception as table_err:
                    print(f"❌ {table_name} kopyalanırken atlandı: {table_err}")

        local_conn.close()
        
        # Temp dosyasını kalıcı yedekle yer değiştir
        if os.path.exists(local_db_path):
            os.remove(local_db_path)
        os.rename(temp_db_path, local_db_path)
        
        print(f"\n🎉 OKUNABİLİR YEDEKLEME BAŞARILI!")
        print(f"Toplam {kopyalanan_tablo_sayisi} tablo, {toplam_kayit} veri satırı -> {local_db_path} içine yazıldı.")
        
    except Exception as fatal:
        local_conn.close()
        print(f"Kritik Hata: Supabase bağlantısı koptu veya reddedildi. {fatal}")

if __name__ == "__main__":
    run_backup()
