import toml
from sqlalchemy import create_engine, text

def check_label():
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["streamlit"]["DB_URL"]
    engine = create_engine(url)
    
    with engine.connect() as conn:
        res = conn.execute(text("SELECT modul_anahtari, modul_etiketi FROM public.ayarlar_moduller WHERE modul_anahtari = 'qdms'")).fetchone()
        if res:
            print(f"Key: {res[0]}")
            print(f"Label: {res[1]}")
            print(f"Label Repr: {repr(res[1])}")
            print(f"Unicode: {res[1].encode('unicode_escape')}")
        else:
            print("QDMS module not found in ayarlar_moduller!")

if __name__ == "__main__":
    check_label()
