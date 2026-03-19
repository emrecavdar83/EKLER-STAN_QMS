
from sqlalchemy import create_engine, text
import toml

def check_perms():
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    if not db_url:
        db_url = 'sqlite:///ekleristan_local.db'
    
    engine = create_engine(db_url)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM ayarlar_yetkiler WHERE rol_adi IN ('OPERATÖR', 'OPERATOR')")).fetchall()
        print(f"Permissions for OPERATÖR:")
        for r in res:
            print(r)

if __name__ == "__main__":
    check_perms()
