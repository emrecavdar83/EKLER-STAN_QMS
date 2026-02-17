from sqlalchemy import create_engine, text
import pandas as pd
import sys

# Force UTF-8 for stdout just in case, though file writing is preferred
sys.stdout.reconfigure(encoding='utf-8')

# Connect to the database
db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

def run_query(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

with open("debug_kpi_output_utf8.txt", "w", encoding="utf-8") as f:
    f.write("--- 1. 'bsahin' Kullanıcısının Tüm Kayıtları ---\n")
    sql_user = "SELECT id, tarih, saat, urun, karar, kullanici FROM urun_kpi_kontrol WHERE kullanici LIKE '%bsahin%' OR kullanici LIKE '%BSAHIN%' ORDER BY id DESC"
    df_user = run_query(sql_user)
    f.write(df_user.to_string() + "\n")

    f.write("\n--- 2. 17.02.2025 Tarihli Tüm Kayıtlar ---\n")
    sql_date_2025 = "SELECT id, tarih, saat, urun, karar, kullanici FROM urun_kpi_kontrol WHERE tarih LIKE '2025-02-17%'"
    df_2025 = run_query(sql_date_2025)
    f.write(df_2025.to_string() + "\n")

    f.write("\n--- 3. 17.02.2026 Tarihli Tüm Kayıtlar (Gelecek/Hatalı Yıl?) ---\n")
    sql_date_2026 = "SELECT id, tarih, saat, urun, karar, kullanici FROM urun_kpi_kontrol WHERE tarih LIKE '2026-02-17%'"
    df_2026 = run_query(sql_date_2026)
    f.write(df_2026.to_string() + "\n")

    f.write("\n--- 4. Son 20 Kayıt (Genel Kontrol) ---\n")
    sql_recent = "SELECT id, tarih, saat, urun, karar, kullanici FROM urun_kpi_kontrol ORDER BY id DESC LIMIT 20"
    df_recent = run_query(sql_recent)
    f.write(df_recent.to_string() + "\n")

    f.write("\n--- 5. Tablo Şeması (Kolon Tipleri) ---\n")
    try:
        sql_schema = "PRAGMA table_info(urun_kpi_kontrol)"
        df_schema = run_query(sql_schema)
        # Convert to string to avoid potential encoding issues with object types
        f.write(df_schema[['name', 'type']].to_string() + "\n")
    except Exception as e:
        f.write(f"Şema okuma hatası: {e}\n")

print("Output written to debug_kpi_output_utf8.txt")
