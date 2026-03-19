import toml
from sqlalchemy import create_engine, text

def diagnose():
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["streamlit"]["DB_URL"]
    engine = create_engine(url)
    
    with engine.connect() as conn:
        print("--- AYARLAR_MODULLER ---")
        res = conn.execute(text("SELECT modul_anahtari, modul_etiketi, aktif FROM public.ayarlar_moduller ORDER BY sira_no")).fetchall()
        for r in res:
            print(f"Modul: {r[0]} | Etiket: {r[1]} | Aktif: {r[2]}")
            
        print("\n--- ADMIN PERMISSIONS IN AYARLAR_YETKILER ---")
        res2 = conn.execute(text("SELECT modul_adi, erisim_turu FROM public.ayarlar_yetkiler WHERE UPPER(rol_adi) = 'ADMIN'")).fetchall()
        for r in res2:
            print(f"Modul: {r[0]} | Yetki: {r[1]}")

if __name__ == "__main__":
    diagnose()
