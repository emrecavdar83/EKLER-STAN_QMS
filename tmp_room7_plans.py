from sqlalchemy import create_engine, text
import pandas as pd

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- -18 DONUK DEPO 2 (ID: 7) Plan Analizi ---")
    res = conn.execute(text("""
        SELECT p.id, p.beklenen_zaman, p.durum, p.gerceklesen_olcum_id, m.sicaklik_degeri, m.olcum_zamani
        FROM olcum_plani p
        LEFT JOIN sicaklik_olcumleri m ON p.gerceklesen_olcum_id = m.id
        WHERE p.oda_id = 7 AND p.beklenen_zaman >= '2026-03-11'
        ORDER BY p.beklenen_zaman DESC
    """)).fetchall()
    
    df = pd.DataFrame([dict(r._mapping) for r in res])
    print(df)
