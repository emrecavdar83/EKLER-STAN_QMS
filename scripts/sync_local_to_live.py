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
    "ayarlar_bolumler",
    "ayarlar_yetkiler",
    "personel",
    "personel_vardiya_programi",
    "ayarlar_temizlik_plani",
    "lokasyonlar",
    "proses_tipleri",
    "lokasyon_proses_atama",
    "tanim_metotlar",
    "kimyasal_envanter",
    "gmp_soru_havuzu",
    "ayarlar_urunler"
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
            
            if table == "personel":
                # Special handling for Self-Referencing Foreign Key (yonetici_id)
                # 1. Backup logic
                df_temp = df_local.copy()
                if 'yonetici_id' in df_temp.columns:
                    # Store original values
                    original_managers = df_temp[['id', 'yonetici_id']].dropna()
                    # Set to NULL to allow insertion
                    df_temp['yonetici_id'] = None
                    
                    # 2. Insert with NULLs
                    df_temp.to_sql(table, conn, if_exists='append', index=False)
                    
                    # 3. Update Manager IDs
                    print("   -> Yonetici ID'leri guncelleniyor...")
                    # We need to do this efficiently. 
                    # For massive datasets, temporary table is better. For <1000 rows, loop is okay-ish or CASE statement.
                    # Let's use a loop with parameters for now, it's safer/easier to implement quickly.
                    update_sql = text("UPDATE personel SET yonetici_id = :yid WHERE id = :pid")
                    
                    # Convert to list of dicts for executemany
                    params_list = [{'yid': int(row['yonetici_id']), 'pid': int(row['id'])} for _, row in original_managers.iterrows()]
                    
                    if params_list:
                         conn.execute(update_sql, params_list)
                else:
                     df_temp.to_sql(table, conn, if_exists='append', index=False)
            else:
                df_local.to_sql(table, conn, if_exists='append', index=False)
            
        print(f"   [OK] {table} basariyla esitlendi!")
        
    except Exception as e:
        print(f"   [HATA] {table}: {e}")

print("\n[BITTI] Islem tamamlandi. Lutfen canli uygulamayi kontrol edin.")
