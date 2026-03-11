from sqlalchemy import create_engine, text
import pandas as pd

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- -18 DONUK DEPO 2 (ID: 7) Ölçüm Detayları ---")
    res = conn.execute(text("""
        SELECT m.id, m.sicaklik_degeri, m.olcum_zamani, m.planlanan_zaman, m.sapma_var_mi, m.is_takip, m.sapma_aciklamasi, p.id as plan_id
        FROM sicaklik_olcumleri m
        LEFT JOIN olcum_plani p ON m.id = p.gerceklesen_olcum_id
        WHERE m.oda_id = 7
        ORDER BY m.olcum_zamani DESC LIMIT 10
    """)).fetchall()
    
    df = pd.DataFrame([dict(r._mapping) for r in res])
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df)
