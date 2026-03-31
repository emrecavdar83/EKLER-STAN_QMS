import sys
import os

# Mevcut çalışma dizinini PYTHONPATH'e ekle
sys.path.append(os.getcwd())

from database.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.begin() as conn:
    print("Checking 'sistem_oturum_izleri' table...")
    # Check if son_modul exists
    columns = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'sistem_oturum_izleri'
    """)).fetchall()
    column_names = [r[0] for r in columns]
    
    if 'son_modul' not in column_names:
        print("Adding 'son_modul' column...")
        conn.execute(text("ALTER TABLE sistem_oturum_izleri ADD COLUMN son_modul VARCHAR(100) DEFAULT 'portal'"))
    else:
        print("'son_modul' column already exists.")

    if 'son_erisim_ts' not in column_names:
        print("Adding 'son_erisim_ts' column...")
        conn.execute(text("ALTER TABLE sistem_oturum_izleri ADD COLUMN son_erisim_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    else:
        print("'son_erisim_ts' column already exists.")
    
    print("Migration completed.")
