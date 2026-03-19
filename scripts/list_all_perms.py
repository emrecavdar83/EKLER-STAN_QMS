import toml
from sqlalchemy import create_engine, text

def list_all():
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["streamlit"]["DB_URL"]
    engine = create_engine(url)
    
    with engine.connect() as conn:
        print("--- ALL MODULES ---")
        res = conn.execute(text("SELECT modul_anahtari, modul_etiketi, aktif, sira_no FROM public.ayarlar_moduller ORDER BY sira_no")).fetchall()
        for r in res:
            print(f"Sira: {r[3]} | Modul: {r[0]} | Etiket: {r[1]} | Aktif: {r[2]}")
            
        print("\n--- ALL ADMIN PERMS ---")
        res2 = conn.execute(text("SELECT modul_adi, erisim_turu FROM public.ayarlar_yetkiler WHERE UPPER(rol_adi) = 'ADMIN'")).fetchall()
        for r in res2:
            print(f"Modul: {r[0]} | Yetki: {r[1]}")

if __name__ == "__main__":
    list_all()
