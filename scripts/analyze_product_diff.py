
import toml
import sqlalchemy
import pandas as pd

def analyze_live_products():
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
    engine = sqlalchemy.create_engine(url.strip('\"'))
    
    # Get live data
    df_live = pd.read_sql("SELECT * FROM ayarlar_urunler", engine)
    
    # Get local data
    import sqlite3
    conn_local = sqlite3.connect('ekleristan_local.db')
    df_local = pd.read_sql("SELECT * FROM ayarlar_urunler", conn_local)
    conn_local.close()
    
    print(f"Live row count: {len(df_live)}")
    print(f"Local row count: {len(df_local)}")
    
    live_unique = set(df_live['urun_adi'].unique())
    local_unique = set(df_local['urun_adi'].unique())
    
    missing_in_local = live_unique - local_unique
    missing_in_live = local_unique - live_unique
    
    print(f"\nUnique products in Live: {len(live_unique)}")
    print(f"Unique products in Local: {len(local_unique)}")
    
    if missing_in_local:
        print(f"\nProducts in Live but NOT in Local ({len(missing_in_local)}):")
        for p in sorted(list(missing_in_local)):
            count = len(df_live[df_live['urun_adi'] == p])
            print(f" - {p} (count in live: {count})")
            
    if missing_in_live:
        print(f"\nProducts in Local but NOT in Live ({len(missing_in_live)}):")
        for p in sorted(list(missing_in_live)):
            print(f" - {p}")

if __name__ == "__main__":
    analyze_live_products()
