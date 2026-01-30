import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

SECRETS_PATH = ".streamlit/secrets.toml"
secrets = toml.load(SECRETS_PATH)
DB_URL = secrets["streamlit"]["DB_URL"]
if DB_URL.startswith('"') and DB_URL.endswith('"'):
    DB_URL = DB_URL[1:-1]

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("--- LIVE DB DIAGNOSTICS ---")
    
    # 1. Toplam Personel
    total = conn.execute(text("SELECT count(*) FROM personel")).scalar()
    print(f"Total Personnel: {total}")
    
    # 2. Aktif Personel
    active = conn.execute(text("SELECT count(*) FROM personel WHERE UPPER(TRIM(durum)) = 'AKTİF'")).scalar()
    print(f"Active Personnel: {active}")
    
    # 3. Ad Soyadı olanlar
    with_name = conn.execute(text("SELECT count(*) FROM personel WHERE ad_soyad IS NOT NULL")).scalar()
    print(f"With Name: {with_name}")
    
    # 4. Departman ID'si olanlar
    with_dept = conn.execute(text("SELECT count(*) FROM personel WHERE departman_id IS NOT NULL")).scalar()
    print(f"With Dept ID: {with_dept}")
    
    # 5. View Count
    try:
        view_count = conn.execute(text("SELECT count(*) FROM v_organizasyon_semasi")).scalar()
        print(f"View v_organizasyon_semasi Count: {view_count}")
    except Exception as e:
        print(f"View Error: {e}")

    # 6. Sample problematic records
    print("\nSample records where durum is NOT AKTİF (top 5):")
    res = conn.execute(text("SELECT ad_soyad, durum FROM personel WHERE UPPER(TRIM(durum)) != 'AKTİF' OR durum IS NULL LIMIT 5"))
    for row in res:
        print(f"  - {row[0]}: {row[1]}")
