
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def get_engine_local():
    return create_engine("sqlite:///ekleristan_local.db")

def get_engine_live():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        url = secrets.get("DB_URL") or (secrets.get("streamlit", {}).get("DB_URL"))
        if url:
            if url.startswith('"'): url = url[1:-1]
            return create_engine(url)
    return None

def check_duplicates(engine, label):
    print(f"\n--- Checking {label} Database ---")
    with engine.connect() as conn:
        # 1. Departman Mükerrerliği (UPPER(TRIM()) bazlı)
        query_dept = """
            SELECT UPPER(TRIM(bolum_adi)) as clean_name, COUNT(*) as count
            FROM ayarlar_bolumler
            GROUP BY clean_name
            HAVING COUNT(*) > 1
        """
        duplicates_dept = pd.read_sql(text(query_dept), conn)
        if not duplicates_dept.empty:
            print(f"!! DANGER: Duplicate Departments found in {label}:")
            print(duplicates_dept)
        else:
            print(f"OK: No duplicate departments in {label}.")

        # 2. Personel Mükerrerliği (kullanici_adi bazlı)
        query_pers = """
            SELECT UPPER(TRIM(kullanici_adi)) as clean_user, COUNT(*) as count
            FROM personel
            WHERE kullanici_adi IS NOT NULL AND kullanici_adi != ''
            GROUP BY clean_user
            HAVING COUNT(*) > 1
        """
        duplicates_pers = pd.read_sql(text(query_pers), conn)
        if not duplicates_pers.empty:
            print(f"!! DANGER: Duplicate Personnel Usernames found in {label}:")
            print(duplicates_pers)
        else:
            print(f"OK: No duplicate usernames in {label}.")
            
        return duplicates_dept.empty and duplicates_pers.empty

if __name__ == "__main__":
    local_ok = check_duplicates(get_engine_local(), "LOCAL")
    
    live_engine = get_engine_live()
    if live_engine:
        live_ok = check_duplicates(live_engine, "LIVE")
    else:
        print("❌ Live Engine could not be established.")
        live_ok = False

    if local_ok and live_ok:
        print("\n--- PRE-FLIGHT COMPLETED: All clear to apply UNIQUE constraints. ---")
    else:
        print("\n--- STOP: Duplicates must be resolved before proceeding. ---")
