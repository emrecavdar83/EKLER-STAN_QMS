
import toml
import sqlite3
import sqlalchemy
from sqlalchemy import text, inspect

def analyze_all_tables():
    # Local tables
    local_conn = sqlite3.connect('ekleristan_local.db')
    local_cursor = local_conn.cursor()
    local_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    local_tables = [row[0] for row in local_cursor.fetchall()]
    local_conn.close()

    # Live tables
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
    live_engine = sqlalchemy.create_engine(url.strip('\"'))
    live_inspector = inspect(live_engine)
    live_tables = live_inspector.get_table_names()

    print("--- Database Comparison ---")
    print(f"Local Tables Count: {len(local_tables)}")
    print(f"Live Tables Count: {len(live_tables)}")
    
    synced_tables = [
        "ayarlar_bolumler", "ayarlar_roller", "ayarlar_yetkiler", "proses_tipleri",
        "tanim_metotlar", "ayarlar_kimyasallar", "ayarlar_urunler", "lokasyonlar",
        "gmp_lokasyonlar", "tanim_ekipmanlar", "ayarlar_temizlik_plani", "personel"
    ]
    
    all_known_tables = sorted(list(set(local_tables + live_tables)))
    
    print("\nTable Status:")
    for t in all_known_tables:
        status = []
        if t in local_tables: status.append("Local: OK")
        else: status.append("Local: MISSING")
        
        if t in live_tables: status.append("Live: OK")
        else: status.append("Live: MISSING")
        
        if t in synced_tables: status.append("(Synced)")
        else: status.append("(NOT Synced)")
        
        print(f"{t:30} | {' | '.join(status)}")

if __name__ == "__main__":
    analyze_all_tables()
