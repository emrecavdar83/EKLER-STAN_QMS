
import pandas as pd
from sqlalchemy import create_engine, text

db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

with open('bolum_conflict.txt', 'w', encoding='utf-8') as f:
    with engine.connect() as conn:
        # Fetch both columns explicitly to see differences
        # We simulate the query: SELECT p.bolum, d.bolum_adi ...
        sql = """
        SELECT p.id, p.ad_soyad, p.kullanici_adi, 
               p.bolum as personel_bolum, 
               d.bolum_adi as joined_bolum,
               p.departman_id
        FROM personel p
        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
        WHERE p.rol LIKE '%Sorumlu%' OR p.rol LIKE '%AMİRİ%'
        """
        df = pd.read_sql(sql, conn)
        
        f.write(df.to_string() + "\n")
        
        # Check specifically for Mihrimah Ali
        user = df[df['kullanici_adi'] == 'mihrimah.ali']
        if not user.empty:
            f.write("\n--- DETAILS FOR MIHRIMAH ALI ---\n")
            f.write(user.to_string() + "\n")
