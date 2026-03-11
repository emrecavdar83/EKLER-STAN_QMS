from sqlalchemy import create_engine, text
import json

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- Personel Tablosu Şeması ---")
    res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'personel' ORDER BY ordinal_position"))
    columns = res.fetchall()
    for col in columns:
        print(f"Column: {col[0]:<20} | Type: {col[1]}")
