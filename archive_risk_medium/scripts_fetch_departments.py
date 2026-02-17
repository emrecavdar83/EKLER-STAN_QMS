import sys
import os

# Try to install dependencies if missing (just in case, though unlikely needed if app runs)
try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("SQLAlchemy not found.")
    sys.exit(1)

def get_db_url():
    # 1. Try to read secrets.toml
    secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "DB_URL" in line:
                        # Simple parsing: DB_URL = "postgresql://..."
                        parts = line.split("=", 1)
                        if len(parts) > 1:
                            raw_url = parts[1].strip().strip('"').strip("'")
                            print(f"DEBUG: Found DB_URL in secrets.toml (Protocol: {raw_url.split(':')[0]})")
                            return raw_url
        except Exception as e:
            print(f"Error reading secrets.toml: {e}")
    
    # 2. Fallback to local SQLite
    print("DEBUG: Using local SQLite fallback")
    return 'sqlite:///ekleristan_local.db'

def main():
    db_url = get_db_url()
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("\n--- DEPARTMANLAR (ayarlar_bolumler) ---")
            try:
                result = conn.execute(text("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler ORDER BY id")).fetchall()
                if not result:
                    print("  (Tablo boş)")
                for row in result:
                    parent = f" (Ana: {row[2]})" if row[2] else ""
                    print(f"  [{row[0]}] {row[1]}{parent}")
            except Exception as e:
                print(f"  Hata: {e}")

            print("\n--- LOKASYONLAR (lokasyonlar) ---")
            try:
                result = conn.execute(text("SELECT id, ad, tip, sorumlu_departman FROM lokasyonlar LIMIT 20")).fetchall()
                if not result:
                    print("  (Tablo boş)")
                for row in result:
                    dept = f" -> Dept: {row[3]}" if row[3] else ""
                    print(f"  [{row[0]}] {row[1]} ({row[2]}){dept}")
            except Exception as e:
                print(f"  Hata: {e}")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    main()
