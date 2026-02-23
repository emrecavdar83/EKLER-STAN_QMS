import toml
import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text, inspect

import json

def compare_schemas(output_file='schema_report.json'):
    print("--- Şema Karşılaştırma Başlıyor (JSON Kaydı İle) ---")
    report = {
        "local_tables": [],
        "live_tables": [],
        "missing_in_live": [],
        "missing_in_local": [],
        "column_mismatches": {}
    }
    try:
        # Load secrets
        secrets_path = os.path.join(os.getcwd(), '.streamlit', 'secrets.toml')
        secrets = toml.load(secrets_path)
        url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
        if url.startswith('"') and url.endswith('"'):
            url = url[1:-1]
        
        # Connect to Live
        live_engine = create_engine(url)
        live_inspector = inspect(live_engine)
        live_tables = set(live_inspector.get_table_names())
        report["live_tables"] = list(live_tables)
        
        # Connect to Local
        local_conn = sqlite3.connect('ekleristan_local.db')
        local_cursor = local_conn.cursor()
        local_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        local_tables = set([t[0] for t in local_cursor.fetchall()])
        report["local_tables"] = list(local_tables)
        
        # Missing tables
        report["missing_in_live"] = list(local_tables - live_tables)
        report["missing_in_local"] = list(live_tables - local_tables)
        
        # Column Check for common tables
        common_tables = local_tables.intersection(live_tables)
        local_inspector = inspect(create_engine('sqlite:///ekleristan_local.db'))
        
        for table in common_tables:
            local_cols = {c['name']: str(c['type']) for c in local_inspector.get_columns(table)}
            live_cols = {c['name']: str(c['type']) for c in live_inspector.get_columns(table)}
            
            diff_l = set(local_cols.keys()) - set(live_cols.keys())
            diff_r = set(live_cols.keys()) - set(local_cols.keys())
            
            if diff_l or diff_r:
                report["column_mismatches"][table] = {
                    "missing_in_live": list(diff_l),
                    "missing_in_local": list(diff_r)
                }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Rapor kaydedildi: {output_file}")
        local_conn.close()
        
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    compare_schemas()
