import toml
import os
from sqlalchemy import create_engine, text

def check():
    try:
        secrets_path = os.path.join(os.getcwd(), '.streamlit', 'secrets.toml')
        secrets = toml.load(secrets_path)
        url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
        if url.startswith('"') and url.endswith('"'):
            url = url[1:-1]
            
        engine = create_engine(url)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM personel WHERE durum = 'AKTİF'")).fetchone()[0]
            print(f"LIVE_COUNT:{res}")
            
            # Mükerrer kontrolü
            res_dup = conn.execute(text("SELECT COUNT(*) FROM (SELECT ad_soyad FROM personel WHERE durum = 'AKTİF' GROUP BY ad_soyad HAVING COUNT(*) > 1) AS dups")).fetchone()[0]
            print(f"LIVE_DUPLICATES:{res_dup}")
            
    except Exception as e:
        print(f"ERROR:{e}")

if __name__ == "__main__":
    check()
