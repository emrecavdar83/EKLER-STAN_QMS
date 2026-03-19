
from sqlalchemy import create_engine, text
import toml
import sys

def check_gulay():
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    if not db_url:
        db_url = 'sqlite:///ekleristan_local.db'
    
    engine = create_engine(db_url)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT kullanici_adi, ad_soyad, durum, rol, departman_id FROM personel WHERE kullanici_adi = 'ggem'")).fetchone()
        if res:
            print(f"Username: {res[0]}")
            print(f"Name: {res[1]}")
            print(f"Status: {res[2]}")
            print(f"Role: {res[3]}")
            print(f"Dept ID: {res[4]}")
        else:
            print("User not found.")

if __name__ == "__main__":
    check_gulay()
