from sqlalchemy import create_engine, text

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("Executing LOCATION migration...")
        
        # 1. lokasyonlar table (col: ad)
        conn.execute(text("UPDATE lokasyonlar SET ad = REPLACE(ad, 'KEK', 'PANDİSPANYA') WHERE ad LIKE '%KEK%'"))
        conn.execute(text("UPDATE lokasyonlar SET ad = REPLACE(ad, 'Kek', 'PANDİSPANYA') WHERE ad LIKE '%Kek%'"))
        
        # 2. gmp_lokasyonlar table (col: lokasyon_adi)
        conn.execute(text("UPDATE gmp_lokasyonlar SET lokasyon_adi = REPLACE(lokasyon_adi, 'KEK', 'PANDİSPANYA') WHERE lokasyon_adi LIKE '%KEK%'"))
        conn.execute(text("UPDATE gmp_lokasyonlar SET lokasyon_adi = REPLACE(lokasyon_adi, 'Kek', 'PANDİSPANYA') WHERE lokasyon_adi LIKE '%Kek%'"))
        
        conn.commit()
        print("Migration executed successfully: Locations KEK -> PANDISPANYA")
except Exception as e:
    print(f"Migration failed: {e}")
