
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
            # fotograf_b64 kolonunu da kontrol et (BRC uyumlu kalici kanit)
                if "fotograf_b64" not in cols:
                    conn.execute(text("ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_b64 TEXT"))
                    conn.commit()
                    logger.info("fotograf_b64 kolonu local DB'ye eklendi (BRC uyumlu).")
    except Exception as e:
        logger.error(f"Error updating local schema: {e}")

    # 2. Live Schema Update
    live_url = get_live_url()
    if live_url:
        live_url = live_url.strip('"')
        live_engine = create_engine(live_url)
        try:
            with live_engine.begin() as conn:
                # fotograf_yolu kontrol
                check_sql = """
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'urun_kpi_kontrol' AND column_name = 'fotograf_yolu'
                """
                count = conn.execute(text(check_sql)).scalar()
                if count == 0:
                    logger.info("Adding fotograf_yolu column to live urun_kpi_kontrol...")
                    conn.execute(text("ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_yolu TEXT"))
                    logger.info("Live schema updated: fotograf_yolu.")
                else:
                    logger.info("fotograf_yolu column already exists in live DB.")

                # fotograf_b64 kontrol (BRC uyumlu kalici kanit)
                check_b64 = """
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'urun_kpi_kontrol' AND column_name = 'fotograf_b64'
                """
                count_b64 = conn.execute(text(check_b64)).scalar()
                if count_b64 == 0:
                    logger.info("Adding fotograf_b64 column to live urun_kpi_kontrol (BRC)...")
                    conn.execute(text("ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_b64 TEXT"))
                    logger.info("Live schema updated: fotograf_b64 eklendi.")
                else:
                    logger.info("fotograf_b64 already exists in live DB.")
        except Exception as e:
            logger.error(f"Error updating live schema: {e}")
    else:
        logger.warning("Live DB URL not found, skipping live update.")


if __name__ == "__main__":
    update_schema()
