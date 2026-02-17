
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def migrate_db(engine, label):
    print(f"--- Migrating {label} ---")
    with engine.connect() as conn:
        # 1. Add Column if missing
        try:
            # Check safely
            try:
                conn.execute(text("SELECT tur FROM ayarlar_bolumler LIMIT 1"))
                print("Column 'tur' already exists.")
            except:
                print("Adding column 'tur'...")
                conn.execute(text("ALTER TABLE ayarlar_bolumler ADD COLUMN tur VARCHAR(50)"))
                conn.commit()
        except Exception as e:
            print(f"Schema check error: {e}")

        # 2. Update Types
        # Logic: Depo -> DEPO, Yönetim/İnsan/Planlama/Kalite -> İDARİ, Temizlik/Bakım/Servis -> HİZMET, Rest -> ÜRETİM
        
        updates = [
            ("DEPO", "bolum_adi LIKE '%DEPO%' OR bolum_adi LIKE '%AMBAR%'"),
            ("İDARİ", "bolum_adi IN ('YÖNETİM', 'İNSAN KAYNAKLARI', 'PLANLAMA', 'KALİTE', 'MUHASEBE')"),
            ("HİZMET", "bolum_adi IN ('TEMİZLİK', 'BAKIM', 'BULAŞIKHANE', 'YEMEKHANE', 'TEKNİK', 'GÜVENLİK', 'OKUL - SERVİS') OR bolum_adi LIKE '%SERVİS%'"),
            # Make sure 'OKUL PROJESİ' remains ÜRETİM (Default) or explicit?
            # It falls to default if not matched above.
        ]
        
        for tur, condition in updates:
            sql = text(f"UPDATE ayarlar_bolumler SET tur = :t WHERE ({condition})")
            res = conn.execute(sql, {"t": tur})
            print(f"Marked {res.rowcount} as {tur}")
            
        # Default remainder to ÜRETİM
        sql_def = text("UPDATE ayarlar_bolumler SET tur = 'ÜRETİM' WHERE tur IS NULL")
        res_def = conn.execute(sql_def)
        print(f"Marked {res_def.rowcount} as ÜRETİM (Default)")
        
        # 3. Create 'OKUL - SERVİS' if missing (For Systematic Separation)
        # Check parent 21 exists
        res_p = conn.execute(text("SELECT id FROM ayarlar_bolumler WHERE id=21")).fetchone()
        if res_p:
            # Check child 2102
            res_c = conn.execute(text("SELECT id FROM ayarlar_bolumler WHERE id=2102")).fetchone()
            if not res_c:
                print("Creating 'OKUL - SERVİS' (HİZMET)...")
                conn.execute(text("INSERT INTO ayarlar_bolumler (id, bolum_adi, ana_departman_id, aktif, sira_no, tur) VALUES (2102, 'OKUL - SERVİS', 21, 1, 2, 'HİZMET')"))
            else:
                 # Ensure it is HİZMET
                 conn.execute(text("UPDATE ayarlar_bolumler SET tur='HİZMET' WHERE id=2102"))
                 
        conn.commit()

# LOCAL
try:
    local_engine = create_engine('sqlite:///ekleristan_local.db')
    migrate_db(local_engine, "LOCAL")
except Exception as e:
    print(f"Local Error: {e}")

# LIVE
try:
    if os.path.exists(".streamlit/secrets.toml"):
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["streamlit"]["DB_URL"]
        if url.startswith('"') and url.endswith('"'): url = url[1:-1]
        
        live_engine = create_engine(url)
        migrate_db(live_engine, "LIVE")
    else:
        print("Live secrets not found.")
except Exception as e:
    print(f"Live Error: {e}")
