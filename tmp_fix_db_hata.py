from sqlalchemy import create_engine, text

# Local DB engine
engine = create_engine("sqlite:///c:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db")

def fix_hata_loglari():
    try:
        with engine.begin() as conn:
            # Kolon kontrolü (PRAGMA table_info için 'engine.connect()' bazen daha iyi)
            print("Checking columns in hata_loglari...")
            res = conn.execute(text("PRAGMA table_info(hata_loglari)")).fetchall()
            columns = [r[1] for r in res]
            
            if 'ai_diagnosis' not in columns:
                print("Adding 'ai_diagnosis' column...")
                conn.execute(text("ALTER TABLE hata_loglari ADD COLUMN ai_diagnosis TEXT"))
            
            if 'kullanici_id' not in columns:
                print("Adding 'kullanici_id' column...")
                conn.execute(text("ALTER TABLE hata_loglari ADD COLUMN kullanici_id INTEGER DEFAULT 0"))
            
            print("SUCCESS: hata_loglari table updated.")
            
    except Exception as e:
        print(f"ERROR: Column addition failed: {e}")

if __name__ == "__main__":
    fix_hata_loglari()
