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
        # Get admin ID
        res = conn.execute(text("SELECT id FROM personel WHERE kullanici_adi = 'Admin'")).fetchone()
        admin_id = res[0] if res else 1
        
        # Check if task already exists today to prevent duplication (test running twice)
        today = date.today().isoformat()
        
        # Seed test task into birlesik_gorev_havuzu
        insert_sql = text("""
            INSERT INTO birlesik_gorev_havuzu (personel_id, bolum_id, gorev_adi, gorev_kaynagi, atama_tarihi, durum)
            VALUES (:pid, 0, 'Canlı Modül Otonom Test Görevi', 'Sistem_Ajanı', :tarih, 'BEKLIYOR')
        """)
        conn.execute(insert_sql, {"pid": admin_id, "tarih": today})
        print(f"Test gorevi Admin (ID: {admin_id}) icin {today} tarihine eklendi.")
except Exception as e:
    print(f"Test Verisi Ekleme Hatasi: {e}")
