
import toml
from sqlalchemy import create_engine, text

def run_fix():
    try:
        secrets = toml.load('.streamlit/secrets.toml')
        db_url = secrets['streamlit']['DB_URL']
        engine = create_engine(db_url)
        with engine.begin() as conn:
            # Personel Tablosu
            q1 = "UPDATE personel SET rol = UPPER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(rol, 'i', 'I'), 'ı', 'I'), 'İ', 'I'), 'ü', 'U'), 'ö', 'O'), 'ç', 'C')) WHERE rol IS NOT NULL"
            q2 = "UPDATE personel SET rol = 'KALITE SORUMLUSU' WHERE rol LIKE 'KALITE SORUMLSU%'"
            # Ayarlar Yetkiler
            q3 = "UPDATE ayarlar_yetkiler SET rol_adi = UPPER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(rol_adi, 'i', 'I'), 'ı', 'I'), 'İ', 'I'), 'ü', 'U'), 'ö', 'O'), 'ç', 'C')) WHERE rol_adi IS NOT NULL"
            q4 = "UPDATE ayarlar_yetkiler SET rol_adi = 'KALITE SORUMLUSU' WHERE rol_adi LIKE 'KALITE SORUMLSU%'"
            
            conn.execute(text(q1))
            conn.execute(text(q2))
            conn.execute(text(q3))
            conn.execute(text(q4))
            print("Migration Successful")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_fix()
