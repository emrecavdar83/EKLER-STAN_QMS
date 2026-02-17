
from sqlalchemy import create_engine, text
import toml
import os

def force_live_update():
    print("--- LIVE DB MIGRATION ---")
    try:
        if os.path.exists(".streamlit/secrets.toml"):
            secrets = toml.load(".streamlit/secrets.toml")
            url = secrets["streamlit"]["DB_URL"]
            # Clean URL
            if url.startswith('"') and url.endswith('"'): url = url[1:-1]
            
            engine = create_engine(url)
            with engine.connect() as conn:
                # 1. ADD COLUMN
                try:
                    print("Attempting to add 'tur' column...")
                    conn.execute(text("ALTER TABLE ayarlar_bolumler ADD COLUMN tur VARCHAR(50)"))
                    conn.commit()
                    print("SUCCESS: Column 'tur' added.")
                except Exception as e:
                    # Ignore if exists (Postgres raises CheckViolation or DuplicateColumn)
                    print(f"INFO: Column add skipped (Likely exists). Msg: {str(e)[:50]}...")
                    conn.rollback()

                # 2. UPDATE DATA
                try:
                    print("Classifying departments...")
                    # DEPO
                    conn.execute(text("UPDATE ayarlar_bolumler SET tur = 'DEPO' WHERE bolum_adi LIKE '%DEPO%' OR bolum_adi LIKE '%AMBAR%'"))
                    
                    # İDARİ
                    conn.execute(text("UPDATE ayarlar_bolumler SET tur = 'İDARİ' WHERE bolum_adi IN ('YÖNETİM', 'MUHASEBE', 'PLANLAMA', 'KALİTE', 'İNSAN KAYNAKLARI')"))
                    
                    # HİZMET (Includes OKUL - SERVİS)
                    conn.execute(text("UPDATE ayarlar_bolumler SET tur = 'HİZMET' WHERE bolum_adi LIKE '%SERVİS%' OR bolum_adi LIKE '%TEMİZLİK%' OR bolum_adi LIKE '%BAKIM%' OR bolum_adi LIKE '%GÜVENLİK%' OR bolum_adi LIKE '%YEMEKHANE%'"))
                    
                    # ÜRETİM (Default for rest)
                    conn.execute(text("UPDATE ayarlar_bolumler SET tur = 'ÜRETİM' WHERE tur IS NULL"))
                    
                    conn.commit()
                    print("SUCCESS: Departments classified.")
                    
                    # Verify
                    res = conn.execute(text("SELECT bolum_adi, tur FROM ayarlar_bolumler LIMIT 5")).fetchall()
                    print("Sample Data:", res)
                    
                except Exception as e:
                    print(f"ERROR: Data update failed: {e}")
                    conn.rollback()
        else:
            print("ERROR: Secrets file not found.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    force_live_update()
