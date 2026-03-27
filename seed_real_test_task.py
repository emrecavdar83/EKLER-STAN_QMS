import toml
from sqlalchemy import create_engine, text
from datetime import date
import os

try:
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    if url.startswith('"') and url.endswith('"'): url = url[1:-1]
    
    engine = create_engine(url)
    with engine.begin() as conn:
        today = date.today().isoformat()
        
        # 1. Insert fake task into catalog
        res_cat = conn.execute(text("""
            INSERT INTO gunluk_gorev_katalogu (kod, ad, kategori, periyot)
            VALUES ('TEST_01', 'Canlı Modül Otonom Test Görevi', 'Sistem', 'gunluk')
            ON CONFLICT (kod) DO UPDATE SET ad='Canlı Modül Otonom Test Görevi'
            RETURNING id
        """)).fetchone()
        k_id = res_cat[0]
        
        # 2. Assign task to Admin
        res_adm = conn.execute(text("SELECT id FROM personel WHERE kullanici_adi = 'Admin'")).fetchone()
        admin_id = res_adm[0] if res_adm else 1
        
        conn.execute(text("""
            INSERT INTO birlesik_gorev_havuzu (personel_id, bolum_id, gorev_kaynagi, kaynak_id, atanma_tarihi, hedef_tarih, durum)
            VALUES (:pid, 0, 'PERIYODIK', :kid, :tarih, :tarih, 'BEKLIYOR')
            ON CONFLICT DO NOTHING
        """), {"pid": admin_id, "kid": k_id, "tarih": today})
        
        print(f"Test gorevi Admin'e (PID:{admin_id}, KID:{k_id}) basariyla eklendi.")
except Exception as e:
    print(f"Hata: {e}")
