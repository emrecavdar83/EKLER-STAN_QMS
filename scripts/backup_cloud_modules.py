import os, sys
sys.path.append(os.getcwd())
import streamlit as st
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine

def backup_cloud_modules():
    print("Initiating Cloud Module Backup...")
    engine = get_engine()
    is_pg = engine.dialect.name == 'postgresql'
    
    if not is_pg:
        print("Error: Current engine is not PostgreSQL (Cloud). Check your secrets/config.")
        return

    try:
        with engine.connect() as conn:
            sql = "SELECT id, modul_anahtari, modul_etiketi, sira_no, aktif FROM ayarlar_moduller ORDER BY sira_no"
            df = pd.read_sql(text(sql), conn)
            
            output_file = "cloud_backup_moduller.txt"
            # Ensure UTF-8 writing
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("BACKUP: ayarlar_moduller (Cloud - Supabase)\n")
                f.write(f"DATE: {pd.Timestamp.now()}\n")
                f.write("-" * 50 + "\n")
                f.write(df.to_string(index=False))
                f.write("\n" + "-" * 50 + "\n")
            
            print(f"Backup successful: {output_file}")
            # Use safe printing for Windows console
            try:
                print(f"Rows found: {len(df)}")
                print("\nContent Preview (Encoded):")
                print(df.to_string(index=False).encode('ascii', errors='replace').decode())
            except:
                print("Preview skipped due to console encoding limits.")
            
    except Exception as e:
        print(f"Backup failed: {e}")

if __name__ == "__main__":
    backup_cloud_modules()
