
import toml
import sqlite3
import sqlalchemy
from sqlalchemy import text
import pandas as pd

def detailed_diff():
    # Live
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
    live_engine = sqlalchemy.create_engine(url.strip('\"'))
    
    # Local
    local_conn = sqlite3.connect('ekleristan_local.db')
    
    # 1. ayarlar_bolumler
    df_l_bolum = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", local_conn)
    df_r_bolum = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", live_engine)
    
    print("--- ayarlar_bolumler DIFF ---")
    live_only = df_r_bolum[~df_r_bolum['bolum_adi'].isin(df_l_bolum['bolum_adi'])]
    local_only = df_l_bolum[~df_l_bolum['bolum_adi'].isin(df_r_bolum['bolum_adi'])]
    print(f"Live Only Departments: {live_only['bolum_adi'].tolist()}")
    print(f"Local Only Departments: {local_only['bolum_adi'].tolist()}")

    # 2. ayarlar_roller
    df_l_rol = pd.read_sql("SELECT id, rol_adi FROM ayarlar_roller", local_conn)
    df_r_rol = pd.read_sql("SELECT id, rol_adi FROM ayarlar_roller", live_engine)
    
    print("\n--- ayarlar_roller DIFF ---")
    live_only_rol = df_r_rol[~df_r_rol['rol_adi'].isin(df_l_rol['rol_adi'])]
    print(f"Live Only Roles: {live_only_rol['rol_adi'].tolist()}")

    # 3. Sample of Products (Why so many in live?)
    df_r_urun = pd.read_sql("SELECT urun_adi FROM ayarlar_urunler LIMIT 10", live_engine)
    print("\n--- ayarlar_urunler (Live Sample) ---")
    print(df_r_urun['urun_adi'].tolist())

    local_conn.close()

if __name__ == "__main__":
    detailed_diff()
