import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///ekleristan_local.db')

with engine.connect() as conn:
    print("=== PERSONEL TABLOSU SÜTUNLARI ===")
    try:
        df = pd.read_sql("SELECT * FROM personel LIMIT 5", conn)
        print("Sütunlar:", df.columns.tolist())
        print("\nÖrnek Veriler:")
        print(df.to_string())
        
        print("\n=== MEVCUT GÖREV/ROL DAĞILIMI ===")
        rol_df = pd.read_sql("SELECT rol, COUNT(*) as sayi FROM personel GROUP BY rol ORDER BY sayi DESC", conn)
        print(rol_df.to_string())
    except Exception as e:
        print(f"Hata: {e}")
