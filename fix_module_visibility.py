import toml
from sqlalchemy import create_engine, text

try:
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    if url.startswith('"') and url.endswith('"'): url = url[1:-1]
    
    engine = create_engine(url)
    with engine.begin() as conn:
        # Check active modules
        res = conn.execute(text("SELECT modul_anahtari, aktif, zone FROM ayarlar_moduller")).fetchall()
        print("Mevcut Moduller:")
        for r in res:
            print(f"- {r[0]} | Aktif: {r[1]} | Zone: {r[2]}")
            
        # Hard insert/update for gunluk_gorevler
        conn.execute(text("""
            INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif, zone)
            VALUES ('gunluk_gorevler', ' Günlük Görevler', 85, 1, 'ops')
            ON CONFLICT (modul_anahtari) DO UPDATE SET 
                aktif = 1, zone = 'ops', modul_etiketi = ' Günlük Görevler'
        """))
        print("\n'gunluk_gorevler' modulu basariyla zorunlu aktif edildi.")
        
        # Give permission to Admin just in case
        conn.execute(text("""
            INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu, eylem_yetkileri)
            VALUES ('ADMIN', 'gunluk_gorevler', 'Tam', '{"ekle":true,"guncelle":true,"sil":true}')
            ON CONFLICT (rol_adi, modul_adi) DO NOTHING
        """))
        
except Exception as e:
    print(f"Hata: {e}")
