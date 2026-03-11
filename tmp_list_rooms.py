from sqlalchemy import create_engine, text

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- Tüm Soğuk Odalar ---")
    res = conn.execute(text("SELECT id, oda_adi, oda_kodu FROM soguk_odalar")).fetchall()
    for r in res:
        print(f"ID: {r[0]}, Ad: {r[1]}, Kod: {r[2]}")
        
    print("\n--- Son 10 Ölçüm Kaydı (Tüm Odalar) ---")
    res_m = conn.execute(text("""
        SELECT m.id, o.oda_adi, m.sicaklik_degeri, m.olcum_zamani, m.sapma_var_mi, m.is_takip, m.sapma_aciklamasi 
        FROM sicaklik_olcumleri m
        JOIN soguk_odalar o ON m.oda_id = o.id
        ORDER BY m.olcum_zamani DESC LIMIT 20
    """)).fetchall()
    for r in res_m:
        print(f"ID: {r[0]}, Oda: {r[1]}, Değer: {r[2]}, Zaman: {r[3]}, Sapma: {r[4]}, Takip: {r[5]}, Açıklama: {r[6]}")
