
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def get_live_url():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
            return secrets["streamlit"]["DB_URL"]
        elif "DB_URL" in secrets:
            return secrets["DB_URL"]
    return None

live_url = get_live_url()
if live_url and live_url.startswith('"'): live_url = live_url[1:-1]

live_engine = create_engine(live_url)

with live_engine.connect() as conn:
    print("\n--- FINAL VERIFICATION: LIVE DB ---")
    
    # 1. Durum Values
    df_d = pd.read_sql("SELECT DISTINCT durum FROM personel", conn)
    print("Durum values:", df_d['durum'].tolist())
    
    # 2. Gündüz Vardiyası Personnel Count
    df_cnt = pd.read_sql("""
        SELECT COUNT(*) as count 
        FROM personel 
        WHERE vardiya = 'GÜNDÜZ VARDİYASI' AND durum = 'AKTİF'
    """, conn)
    print(f"Active Personnel in Gündüz Vardiyası: {df_cnt.iloc[0,0]}")

    # 3. Role Breakdown for visibility
    df_rol = pd.read_sql("""
        SELECT rol, COUNT(*) as count 
        FROM personel 
        WHERE vardiya = 'GÜNDÜZ VARDİYASI' AND durum = 'AKTİF'
        GROUP BY rol
    """, conn)
    print("\nRole Breakdown (Visible):")
    print(df_rol)

    # 4. Sample Names (Verify Uppercase)
    df_names = pd.read_sql("""
        SELECT ad_soyad, rol 
        FROM personel 
        WHERE vardiya = 'GÜNDÜZ VARDİYASI' AND durum = 'AKTİF'
        LIMIT 10
    """, conn)
    print("\nSample Personnel (Visible):")
    print(df_names)

    if df_cnt.iloc[0,0] > 100:
        print("\n✅ SUCCESS: Visibility restored for all staff!")
    else:
        print("\n❌ WARNING: Count still seems low.")
