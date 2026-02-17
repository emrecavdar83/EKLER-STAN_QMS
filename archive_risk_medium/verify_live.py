from sqlalchemy import create_engine, text
import toml
import os

SECRETS_PATH = ".streamlit/secrets.toml"
secrets = toml.load(SECRETS_PATH)
url = secrets["streamlit"]["DB_URL"]
if url.startswith('"') and url.endswith('"'): url = url[1:-1]

engine = create_engine(url)

with engine.connect() as conn:
    res = conn.execute(text("SELECT ad_soyad, telefon_no, servis_duragi FROM personel WHERE ad_soyad LIKE '%ABDALRAOUF%'")).fetchone()
    print("Verification Result:", res)
