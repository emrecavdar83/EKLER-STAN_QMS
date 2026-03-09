import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import text
from database.connection import get_engine
import pandas as pd

def check_personnel():
    engine = get_engine()
    print(f"Engine URL: {engine.url}")
    
    with engine.connect() as conn:
        print("\n--- Tüm Departmanlar ---")
        try:
            res = conn.execute(text("SELECT id, bolum_adi FROM ayarlar_bolumler")).fetchall()
            for r in res:
                if 'rulo' in str(r[1]).lower():
                    print(f"RULO PASTA DEPARTMANI BULUNDU: {r}")
                else:
                    print(r)
        except Exception as e:
            print(f"Okuma hatası: {e}")

        print("\n--- Rulo Pasta Personelleri ---")
        try:
            query = """
            SELECT p.ad_soyad, d.bolum_adi, p.vardiya, p.durum 
            FROM personel p 
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id 
            WHERE d.bolum_adi ILIKE '%rulo%' OR p.ad_soyad ILIKE '%rulo%'
            """
            if 'sqlite' in str(engine.url):
                query = query.replace('ILIKE', 'LIKE')
                
            df = pd.read_sql(text(query), conn)
            print(df.to_string())
        except Exception as e:
            print(f"Personel okuma hatası: {e}")

if __name__ == "__main__":
    check_personnel()
