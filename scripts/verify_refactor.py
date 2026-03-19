import toml
from sqlalchemy import create_engine, text

def verify_refactor():
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["streamlit"]["DB_URL"]
    engine = create_engine(url)
    
    with engine.connect() as conn:
        print("--- QDMS MODULE IN AYARLAR_MODULLER ---")
        res = conn.execute(text("SELECT * FROM public.ayarlar_moduller WHERE modul_anahtari = 'qdms'")).fetchall()
        for r in res: print(r)
        
        print("\n--- QDMS PERMS IN AYARLAR_YETKILER ---")
        res2 = conn.execute(text("SELECT rol_adi, erisim_turu FROM public.ayarlar_yetkiler WHERE modul_adi = 'qdms' ORDER BY erisim_turu")).fetchall()
        for r in res2: print(r)

if __name__ == "__main__":
    verify_refactor()
