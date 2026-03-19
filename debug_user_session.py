
from sqlalchemy import create_engine, text
import toml
import sys

def check_user():
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    if not db_url:
        db_url = 'sqlite:///ekleristan_local.db'
    
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # 1. Find the user
        res = conn.execute(text("SELECT kullanici_adi, ad_soyad FROM personel WHERE ad_soyad LIKE '%GÜLAY%' OR ad_soyad LIKE '%GULAY%'")).fetchall()
        print("Matching Users:")
        for r in res:
            print(f"Username: {r[0]}, Name: {r[1]}")
            
        if res:
            username = res[0][0]
            # 2. Check last 50 audit logs for this user
            log_res = conn.execute(text("""
                SELECT zaman, islem_tipi, detay 
                FROM sistem_loglari 
                WHERE detay LIKE :u OR islem_tipi LIKE '%GIRIS%'
                ORDER BY zaman DESC LIMIT 20
            """), {"u": f"%{username}%"}).fetchall()
            print("\nRecent relevant logs:")
            for l in log_res:
                print(l)

if __name__ == "__main__":
    check_user()
