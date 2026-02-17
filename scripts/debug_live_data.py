
import toml
import sqlalchemy
import pandas as pd
import sqlite3

def check_live_data():
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
    engine = sqlalchemy.create_engine(url.strip('\"'))
    
    tables = ['ayarlar_bolumler', 'ayarlar_roller', 'ayarlar_urunler']
    
    for table in tables:
        print(f"\n--- {table} ---")
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        print(f"Row count: {len(df)}")
        if table == 'ayarlar_urunler':
            duplicates = df.duplicated(subset=['urun_adi']).sum()
            print(f"Duplicates in urun_adi: {duplicates}")
            if duplicates > 0:
                print("Sample duplicates:")
                print(df[df.duplicated(subset=['urun_adi'], keep=False)].sort_values('urun_adi').head(10))
        
if __name__ == "__main__":
    check_live_data()
