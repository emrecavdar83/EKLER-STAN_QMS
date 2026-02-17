
import toml
import sqlalchemy
import pandas as pd
import sqlite3

def compare_details():
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
    engine = sqlalchemy.create_engine(url.strip('\"'))
    conn_local = sqlite3.connect('ekleristan_local.db')
    
    for table, pk in [('ayarlar_bolumler', 'bolum_adi'), ('ayarlar_roller', 'rol_adi')]:
        df_live = pd.read_sql(f"SELECT * FROM {table}", engine)
        df_local = pd.read_sql(f"SELECT * FROM {table}", conn_local)
        
        live_set = set(df_live[pk].unique())
        local_set = set(df_local[pk].unique())
        
        diff = live_set - local_set
        if diff:
            print(f"\n{table} in Live but NOT in Local:")
            for item in sorted(list(diff)):
                print(f" - {item}")
        
        diff_local = local_set - live_set
        if diff_local:
            print(f"\n{table} in Local but NOT in Live:")
            for item in sorted(list(diff_local)):
                print(f" - {item}")

if __name__ == "__main__":
    compare_details()
