
from sqlalchemy import create_engine, text
import os
import toml

def get_live_url():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
            return secrets["streamlit"]["DB_URL"]
        elif "DB_URL" in secrets:
            return secrets["DB_URL"]
    return None

url = get_live_url()
if url:
    url = url.strip('"')
    engine = create_engine(url)
    with engine.connect() as conn:
        print("--- Table: urun_kpi_kontrol ---")
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'urun_kpi_kontrol'"))
        for row in res:
            print(f"Column: {row[0]}, Type: {row[1]}")
        
        print("\n--- Table: gmp_denetim_kayitlari (Reference) ---")
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'gmp_denetim_kayitlari'"))
        for row in res:
            print(f"Column: {row[0]}, Type: {row[1]}")
else:
    print("Live DB URL not found.")
