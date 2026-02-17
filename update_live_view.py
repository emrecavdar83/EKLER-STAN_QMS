
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def get_live_url():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
            return secrets["streamlit"]["DB_URL"]
        elif "DB_URL" in secrets:
            return secrets["DB_URL"]
    return None

live_url = get_live_url()
if live_url and live_url.startswith('"'): live_url = live_url[1:-1]

live_engine = create_engine(live_url)

with live_engine.connect() as conn:
    print("Updating 'v_organizasyon_semasi' to handle Turkish UPPER correctly and be robust...")
    
    # In Postgres, we should use UPPER(durum) = 'AKTİF'
    # Actually, after data standardization, even durum = 'AKTİF' would work, 
    # but let's make the view more robust too.
    
    view_sql = """
    CREATE OR REPLACE VIEW v_organizasyon_semasi AS
    SELECT 
        p.id,
        p.ad_soyad,
        p.gorev,
        p.rol,
        p.pozisyon_seviye,
        p.yonetici_id,
        y.ad_soyad AS yonetici_adi,
        p.departman_id,
        d.bolum_adi AS departman,
        p.durum,
        p.vardiya,
        p.kullanici_adi
    FROM personel p
    LEFT JOIN personel y ON p.yonetici_id = y.id
    LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
    WHERE p.ad_soyad IS NOT NULL 
    AND (UPPER(TRIM(p.durum)) = 'AKTİF' OR p.durum IS NULL);
    """
    
    conn.execute(text(view_sql))
    conn.commit()
    print("✅ View updated!")
