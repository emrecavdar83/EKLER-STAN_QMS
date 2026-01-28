import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os
import sys

# Encoding sorunu için
sys.stdout.reconfigure(encoding='utf-8')

# 1. Baglanti Bilgilerini Al
SECRETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "secrets.toml")

try:
    secrets = toml.load(SECRETS_PATH)
    # [streamlit] bolumu altinda mi kontrol et, degilse direkt al
    if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
        LIVE_DB_URL = secrets["streamlit"]["DB_URL"]
    elif "DB_URL" in secrets:
        LIVE_DB_URL = secrets["DB_URL"]
    else:
        raise KeyError("DB_URL not found in secrets")
        
    if LIVE_DB_URL.startswith('"') and LIVE_DB_URL.endswith('"'):
        LIVE_DB_URL = LIVE_DB_URL[1:-1]
except Exception as e:
    print(f"[HATA] Secrets okunamadi: {e}")
    exit(1)

LOCAL_DB_URL = "sqlite:///ekleristan_local.db"

# 2. Baglantilari Kur
print("[BILGI] Baglantilar kuruluyor...")
local_engine = create_engine(LOCAL_DB_URL)

try:
    live_engine = create_engine(LIVE_DB_URL)
    with live_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[OK] Canli baglanti basarili.")
except Exception as e:
    print(f"[HATA] Canli veritabanina baglanilamadi: {e}")
    exit(1)

# 3. Esitlenecek Tablolar
TABLES = [
    "ayarlar_bolumler",      # Departmanlar
    "ayarlar_yetkiler",      # Roller/Yetkiler
    "personel",              # Organizasyon Semasi
    "ayarlar_temizlik_plani" # Varsa
]

print("\n[BILGI] Esitleme baslatiliyor...")

for table in TABLES:
    print(f"\n[ISLEM] {table} isleniyor...")
    try:
        # Lokalen Oku
        df_local = pd.read_sql(f"SELECT * FROM {table}", local_engine)
        count_local = len(df_local)
        print(f"   -> Lokalden okunan kayit: {count_local}")
        
        if df_local.empty:
            print("   -> Tablo bos, atlaniyor.")
            continue

        # Canliya Yaz
        with live_engine.begin() as conn:
            # Once temizle
            print("   -> Canli tablo temizleniyor...")
            conn.execute(text(f"DELETE FROM {table}"))
            
            # Sonra ekle
            print("   -> Veriler yukleniyor...")
            df_local.to_sql(table, conn, if_exists='append', index=False)
            
        print(f"   [OK] {table} basariyla esitlendi!")
        
    except Exception as e:
        print(f"   [HATA] {table}: {e}")

print("\n[BITTI] Islem tamamlandi. Lutfen canli uygulamayi kontrol edin.")
