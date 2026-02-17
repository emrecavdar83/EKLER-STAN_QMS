from sqlalchemy import create_engine, text
import pandas as pd
import os

backup_files = [
    "archive_risk_high/ekleristan_local_backup.db",
    "archive_risk_high/ekleristan_local_backup_20260131_115014.db",
    "ekleristan_local.db.backup_merge_23_22"
]

print("--- SCANNING BACKUPS FOR PASSWORDS ---")

for db_path in backup_files:
    if os.path.exists(db_path):
        print(f"\nChecking: {db_path}")
        try:
            # Connect only if file exists
            engine = create_engine(f'sqlite:///{db_path}')
            with engine.connect() as conn:
                # Check for table existence first
                try:
                    sql = text("SELECT kullanici_adi, sifre FROM personel WHERE kullanici_adi IN ('emre.cavdar', 'Admin')")
                    df = pd.read_sql(sql, conn)
                    if not df.empty:
                        print("FOUND DATA:")
                        print(df.to_string(index=False))
                    else:
                        print("Table exists but user not found.")
                except Exception as query_err:
                    print(f"Query Error (maybe table missing): {query_err}")
        except Exception as e:
            print(f"Connection Error: {e}")
    else:
        print(f"File not found: {db_path}")
