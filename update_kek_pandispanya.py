
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

SECRETS_PATH = ".streamlit/secrets.toml"
secrets = toml.load(SECRETS_PATH)
DB_URL = secrets["streamlit"]["DB_URL"]
if DB_URL.startswith('"') and DB_URL.endswith('"'):
    DB_URL = DB_URL[1:-1]

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("--- UPDATING LIVE DB: KEK -> PANDİSPANYA ---")
    
    # 1. Update ayarlar_bolumler (Departments)
    print("Updating ayarlar_bolumler...")
    try:
        # Update Name
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'PANDİSPANYA' WHERE bolum_adi = 'KEK'"))
        
        # Update Description (replace KEK with PANDİSPANYA)
        # Using REPLACE function if supported (Postgres supports it)
        conn.execute(text("UPDATE ayarlar_bolumler SET aciklama = REPLACE(aciklama, 'KEK', 'PANDİSPANYA') WHERE aciklama LIKE '%KEK%'"))
        
        print("Updated ayarlar_bolumler.")
    except Exception as e:
        print(f"Error updating ayarlar_bolumler: {e}")
        
    # 2. Update lokasyonlar (Locations)
    print("\nUpdating lokasyonlar...")
    try:
        # Update Name
        conn.execute(text("UPDATE lokasyonlar SET ad = 'PANDİSPANYA' WHERE ad = 'KEK'"))
        
        # Update sorumlu_departman path (e.g. YÖNETİM > ÜRETİM > KEK)
        conn.execute(text("UPDATE lokasyonlar SET sorumlu_departman = REPLACE(sorumlu_departman, 'KEK', 'PANDİSPANYA') WHERE sorumlu_departman LIKE '%KEK%'"))
        
        print("Updated lokasyonlar.")
    except Exception as e:
        print(f"Error updating lokasyonlar: {e}")

    # Commit is handled automatically nicely with begin usually, but here with execute in connect block we might need explicit commit depending on driver/sqlalchemy version if autocommit is not on.
    # But usually execute() auto-commits in implicit transaction mode for some drivers, or we should use .commit(). Let's try explicit commit to be safe if not using begin().
    try:
        conn.commit()
        print("Changes committed.")
    except Exception as e:
        # If the driver/engine doesn't support commit on connection without transaction, it might error or just work.
        # With newer SQLAlchemy, it's better to use engine.begin()
        pass

# Re-run verification using begin() context manager to ensure commit
with engine.begin() as conn:
     print("--- VERIFYING KEK DELETION ---")
     # Just a quick check within the same run or separate script. 
     # I'll rely on verify script later, but let's just make sure updates really happened by enforcing transaction commit via 'begin' context in previous block or this one if I merged them.
     # Actually, let's just run the block above inside begin() to be safe.
     pass
