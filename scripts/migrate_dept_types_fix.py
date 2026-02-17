
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def migrate_db(engine, label):
    print(f"--- Migrating {label} ---")
    with engine.connect() as conn:
        # 1. Add Column if missing
        try:
             # Postgres safe check
            try:
                conn.execute(text("SELECT tur FROM ayarlar_bolumler LIMIT 1"))
            except:
                print("Adding column 'tur'...")
                conn.execute(text("ALTER TABLE ayarlar_bolumler ADD COLUMN tur VARCHAR(50)"))
                conn.commit()
        except Exception as e:
            print(f"Schema check error: {e}")

        # 2. Update Types
        # Postgres requires explicit casting or quotes depending on driver? 
        # Actually sqlalchemy handles params. The issue might be LIKE syntax or Transaction.
        
        # 2. Update Types (Specific IDs is safer for Postgres than complex LIKE)
        # But for speed, we try standard SQL
        try:
             # Postgres LIKE is case sensitive usually, but ILIKE is Postgres specific. 
             # We use generic logic or pass via params
             
             # Case 1: DEPO
             conn.execute(text("UPDATE ayarlar_bolumler SET tur = :t WHERE bolum_adi LIKE '%DEPO%' OR bolum_adi LIKE '%AMBAR%'"), {"t": "DEPO"})
             
             # Case 2: İDARİ
             conn.execute(text("UPDATE ayarlar_bolumler SET tur = :t WHERE bolum_adi IN ('YÖNETİM', 'İNSAN KAYNAKLARI', 'PLANLAMA', 'KALİTE', 'MUHASEBE')"), {"t": "İDARİ"})
             
             # Case 3: HİZMET
             # For Postgres, avoid complex ORs if possible or use multiple statements
             conn.execute(text("UPDATE ayarlar_bolumler SET tur = :t WHERE bolum_adi IN ('TEMİZLİK', 'BAKIM', 'BULAŞIKHANE', 'YEMEKHANE', 'TEKNİK', 'GÜVENLİK', 'OKUL - SERVİS')"), {"t": "HİZMET"})
             conn.execute(text("UPDATE ayarlar_bolumler SET tur = :t WHERE bolum_adi LIKE '%SERVİS%' AND tur IS NULL"), {"t": "HİZMET"})
             
             print("Updates executed.")
        except Exception as e:
             print(f"Update error: {e}")
            
        # Default remainder
        sql_def = text("UPDATE ayarlar_bolumler SET tur = 'ÜRETİM' WHERE tur IS NULL")
        res_def = conn.execute(sql_def)
        print(f"Marked remainder as ÜRETİM")
        
        # 3. Create 'OKUL - SERVİS'
        try:
            res_c = conn.execute(text("SELECT id FROM ayarlar_bolumler WHERE id=2102")).fetchone()
            if not res_c:
                print("Creating 'OKUL - SERVİS'...")
                conn.execute(text("INSERT INTO ayarlar_bolumler (id, bolum_adi, ana_departman_id, aktif, sira_no, tur) VALUES (2102, 'OKUL - SERVİS', 21, 1, 2, 'HİZMET')"))
            else:
                 conn.execute(text("UPDATE ayarlar_bolumler SET tur='HİZMET' WHERE id=2102"))
        except Exception as e:
             print(f"Creation error: {e}")
                 
        conn.commit()

# Run Live Only (Local Done)
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
