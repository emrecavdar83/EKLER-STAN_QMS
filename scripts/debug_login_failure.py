from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- USER DEBUG REPORT ---")
        
        # Check Admin and Emre
        sql = text("SELECT id, ad_soyad, kullanici_adi, sifre, rol, durum FROM personel WHERE kullanici_adi IN ('emre.cavdar', 'Admin')")
        df = pd.read_sql(sql, conn)
        
        if df.empty:
            print("❌ NO USERS FOUND! (Admin or emre.cavdar missing)")
        else:
            print(df.to_string())
            
            # Check for duplicates or weird chars
            for idx, row in df.iterrows():
                u = row['kullanici_adi']
                p = row['sifre']
                print(f"\nUser: '{u}' (Len: {len(u)})")
                print(f"Pass: '{p}' (Len: {len(str(p))})")
                
except Exception as e:
    print(f"Error: {e}")
