
import toml
import sqlalchemy
import pandas as pd

def check_live_duplicates():
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
    engine = sqlalchemy.create_engine(url.strip('\"'))
    
    tables = {
        'ayarlar_bolumler': 'bolum_adi',
        'ayarlar_roller': 'rol_adi',
        'ayarlar_urunler': 'urun_adi'
    }
    
    for table, pk in tables.items():
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        dups = df.duplicated(subset=[pk]).sum()
        print(f"Table: {table}, Total Rows: {len(df)}, Duplicates (by {pk}): {dups}")

if __name__ == "__main__":
    check_live_duplicates()
