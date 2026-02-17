from sqlalchemy import create_engine, text
import pandas as pd

try:
    # Try local sqlite
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- SEARCHING LOCAL DB ---")
        
        # Check ayarlar_personel
        sql = text("SELECT * FROM ayarlar_personel WHERE kullanici_adi = 'sevcanalbas'")
        res = conn.execute(sql).fetchall()
        if res:
            print("Found in Ayarlar_Personel:")
            df = pd.DataFrame(res)
            # Try to map columns if possible, but printing raw is fine for debug
            print(res)
        else:
            print("NOT Found in Ayarlar_Personel")

        # Check Personel table (source)
        sql2 = text("SELECT * FROM personel WHERE ad_soyad LIKE '%SEVCAN%' OR ad_soyad LIKE '%sevcan%'")
        res2 = conn.execute(sql2).fetchall()
        if res2:
             print("\nFound in Personel Query (Name Search):")
             for r in res2:
                 print(r)
except Exception as e:
    print(e)
