from sqlalchemy import create_engine, text

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("Executing migration...")
        
        # 1. KEK -> PANDİSPANYA
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = REPLACE(bolum_adi, 'KEK', 'PANDİSPANYA') WHERE bolum_adi LIKE '%KEK%'"))
        
        # 2. Kek -> PANDİSPANYA
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = REPLACE(bolum_adi, 'Kek', 'PANDİSPANYA') WHERE bolum_adi LIKE '%Kek%'"))
        
        conn.commit()
        print("Migration executed successfully: KEK -> PANDISPANYA")
except Exception as e:
    print(f"Migration failed: {e}")
