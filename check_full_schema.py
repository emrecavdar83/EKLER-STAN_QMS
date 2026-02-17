import pandas as pd
from sqlalchemy import create_engine, inspect
import toml
import os

def check_structure():
    local_url = "sqlite:///C:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db"
    secrets_path = r'C:/Projeler/S_program/EKLERİSTAN_QMS/.streamlit/secrets.toml'
    
    secrets = toml.load(secrets_path)
    live_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    
    local_engine = create_engine(local_url)
    live_engine = create_engine(live_url)
    
    local_inspect = inspect(local_engine)
    live_inspect = inspect(live_engine)
    
    tables = ['personel', 'ayarlar_bolumler', 'ayarlar_roller', 'ayarlar_yetkiler', 'lokasyonlar', 'ayarlar_urunler']
    
    print("# VERİTABANI ŞEMA KARŞILAŞTIRMASI\n")
    
    for table in tables:
        l_cols = [c['name'] for c in local_inspect.get_columns(table)]
        r_cols = [c['name'] for c in live_inspect.get_columns(table)]
        
        extra_local = set(l_cols) - set(r_cols)
        extra_live = set(r_cols) - set(l_cols)
        
        if extra_local or extra_live:
            print(f"## Tablo: {table}")
            if extra_local:
                print(f"- **Sadece Lokalde Olanlar:** {', '.join(extra_local)}")
            if extra_live:
                print(f"- **Sadece Canlıda Olanlar:** {', '.join(extra_live)}")
            print("-" * 20)
        else:
            print(f"✅ {table} tablosu şeması birebir aynı.")

if __name__ == "__main__":
    check_structure()
