
from sqlalchemy import create_engine, text
import os
import toml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_live_url():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
            return secrets["streamlit"]["DB_URL"]
        elif "DB_URL" in secrets:
            return secrets["DB_URL"]
    return None

def update_schema():
    # 1. Local Schema Update
    local_url = 'sqlite:///ekleristan_local.db'
    local_engine = create_engine(local_url)
    
    try:
        with local_engine.connect() as conn:
            # Check if column exists
            res = conn.execute(text("PRAGMA table_info(Urun_KPI_Kontrol)")).fetchall()
            cols = [r[1] for r in res]
            if "fotograf_yolu" not in cols:
                logger.info("Adding fotograf_yolu column to local Urun_KPI_Kontrol...")
                conn.execute(text("ALTER TABLE Urun_KPI_Kontrol ADD COLUMN fotograf_yolu TEXT"))
                conn.commit()
                logger.info("Local schema updated.")
            else:
                logger.info("fotograf_yolu column already exists in local DB.")
    except Exception as e:
        logger.error(f"Error updating local schema: {e}")

    # 2. Live Schema Update
    live_url = get_live_url()
    if live_url:
        live_url = live_url.strip('"')
        live_engine = create_engine(live_url)
        try:
            with live_engine.connect() as conn:
                # Check if column exists in Postgres
                check_sql = """
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'urun_kpi_kontrol' AND column_name = 'fotograf_yolu'
                """
                count = conn.execute(text(check_sql)).scalar()
                if count == 0:
                    logger.info("Adding fotograf_yolu column to live urun_kpi_kontrol...")
                    conn.execute(text("ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_yolu TEXT"))
                    conn.commit()
                    logger.info("Live schema updated.")
                else:
                    logger.info("fotograf_yolu column already exists in live DB.")
        except Exception as e:
            logger.error(f"Error updating live schema: {e}")
    else:
        logger.warning("Live DB URL not found, skipping live update.")

if __name__ == "__main__":
    update_schema()
