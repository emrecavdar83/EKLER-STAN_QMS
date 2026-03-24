from sqlalchemy import create_engine, text
import pandas as pd

# Secrets'tan DB_URL'i direkt alalım (Burada manuel yazdım test için, normalde st.secrets'tan gelir)
DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def check_live_db():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # 1. Odalar
            print("--- LIVE ODALAR ---")
            odalar = pd.read_sql(text("SELECT id, oda_kodu, oda_adi, min_sicaklik, max_sicaklik FROM soguk_odalar WHERE aktif = 1"), conn)
            print(odalar)
            
            # 2. Kurallar
            print("\n--- LIVE KURALLAR (ODA ID 1) ---")
            kurallar = pd.read_sql(text("SELECT id, kural_adi, baslangic_saati, bitis_saati, siklik FROM soguk_oda_planlama_kurallari WHERE oda_id = 1 AND aktif = 1"), conn)
            print(kurallar)
            
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    check_live_db()
