import pandas as pd
from sqlalchemy import create_engine
import toml

def get_full_inventory():
    local_url = "sqlite:///C:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db"
    engine = create_engine(local_url)
    tables = ['personel', 'ayarlar_bolumler', 'ayarlar_yetkiler', 'ayarlar_roller', 'ayarlar_urunler', 'lokasyonlar']
    
    print("# VERİTABANI SÜTUN ENVANTERİ (LOKAL)\n")
    for t in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {t} LIMIT 0", engine)
            print(f"### {t}")
            print(f"- **Sütunlar:** {', '.join(df.columns.tolist())}\n")
        except Exception as e:
            print(f"### {t} (Hata: {e})\n")

if __name__ == "__main__":
    get_full_inventory()
