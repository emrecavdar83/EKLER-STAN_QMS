
from sqlalchemy import create_engine, text
import toml
import os

def force_update():
    print("--- FORCE MIGRATION (RETRY) ---")
    if os.path.exists(".streamlit/secrets.toml"):
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["streamlit"]["DB_URL"]
        if url.startswith('"') and url.endswith('"'): url = url[1:-1]
        
        # Use simpler connection arg if needed
        # engine = create_engine(url, connect_args={'sslmode':'require'})
        engine = create_engine(url)
        
        with engine.connect() as conn:
            # 1. ADD COLUMN
            try:
                print("Adding Column 'tur'...")
                # Postgres check column? 
                # Just catch error if exists
                try:
                    conn.execute(text("ALTER TABLE ayarlar_bolumler ADD COLUMN tur VARCHAR(50)"))
                    conn.commit()
                    print("Column Added.")
                except Exception as e:
                    print(f"Column add skipped (Exists?): {str(e)[:100]}")
                    conn.rollback()

            # 2. UPDATE DATA
            try:
                print("Updating Data...")
                # Using simple SQL that works on Postgres
                conn.execute(text("UPDATE ayarlar_bolumler SET tur = 'DEPO' WHERE bolum_adi LIKE '%DEPO%'"))
                conn.execute(text("UPDATE ayarlar_bolumler SET tur = 'İDARİ' WHERE bolum_adi IN ('YÖNETİM', 'MUHASEBE', 'PLANLAMA', 'KALİTE')"))
                conn.execute(text("UPDATE ayarlar_bolumler SET tur = 'HİZMET' WHERE bolum_adi LIKE '%SERVİS%' OR bolum_adi LIKE '%TEMİZLİK%'"))
                conn.execute(text("UPDATE ayarlar_bolumler SET tur = 'ÜRETİM' WHERE tur IS NULL"))
                conn.commit()
                print("Data Updated Successfully.")
            except Exception as e:
                print(f"Update Failed: {e}")
                
if __name__ == "__main__":
    force_update()
