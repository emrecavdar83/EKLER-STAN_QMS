import os
from sqlalchemy import create_engine, text
import pandas as pd

def inspect_live():
    # secrets.toml'daki CANLI linki kullanıyoruz
    db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("\n--- [CANLI DB] PERSONEL KAYITLARI (Emre & Admin) ---")
        try:
            res = conn.execute(text("SELECT id, ad_soyad, kullanici_adi, rol, departman_id, durum FROM personel WHERE ad_soyad ILIKE '%Emre%' OR kullanici_adi = 'Admin'"))
            df = pd.DataFrame(res.fetchall(), columns=res.keys())
            print(df)
        except Exception as e:
            print(f"Hata (Personel): {e}")

        print("\n--- [CANLI DB] DEPARTMANLAR ---")
        try:
            res = conn.execute(text("SELECT id, ad FROM qms_departmanlar"))
            df = pd.DataFrame(res.fetchall(), columns=res.keys())
            print(df)
        except Exception as e:
            print(f"Hata (Departmanlar): {e}")

if __name__ == "__main__":
    inspect_live()
