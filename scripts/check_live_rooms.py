import toml
from sqlalchemy import create_engine, text

SECRETS_FILE = ".streamlit/secrets.toml"

def check_live_room():
    secrets = toml.load(SECRETS_FILE)
    url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    live_engine = create_engine(url)

    print("Checking live rooms...")
    with live_engine.connect() as conn:
        res = conn.execute(text("SELECT id, oda_kodu, oda_adi, aktif FROM soguk_odalar")).fetchall()
        for row in res:
            print(row)

if __name__ == "__main__":
    check_live_room()
