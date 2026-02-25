import pandas as pd
from sqlalchemy import create_engine, text
import toml

LOCAL_DB = "sqlite:///ekleristan_local.db"
SECRETS_FILE = ".streamlit/secrets.toml"

def manual_sync_rooms():
    local_engine = create_engine(LOCAL_DB)
    secrets = toml.load(SECRETS_FILE)
    url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    live_engine = create_engine(url)

    print("Reading local rooms...")
    try:
        df_local = pd.read_sql("SELECT * FROM soguk_odalar", local_engine)
        print(f"Found {len(df_local)} rooms locally.")
        
        with live_engine.begin() as conn:
            for _, row in df_local.iterrows():
                # On conflict update for PostgreSQL
                upsert_sql = text("""
                    INSERT INTO soguk_odalar (oda_kodu, oda_adi, min_sicaklik, max_sicaklik, sapma_takip_dakika, olcum_sikligi, qr_token, aktif)
                    VALUES (:k, :a, :mn, :mx, :t, :s, :qr, :ak)
                    ON CONFLICT (oda_kodu) DO UPDATE SET
                        oda_adi = EXCLUDED.oda_adi,
                        min_sicaklik = EXCLUDED.min_sicaklik,
                        max_sicaklik = EXCLUDED.max_sicaklik,
                        sapma_takip_dakika = EXCLUDED.sapma_takip_dakika,
                        olcum_sikligi = EXCLUDED.olcum_sikligi,
                        qr_token = EXCLUDED.qr_token,
                        aktif = EXCLUDED.aktif
                """)
                conn.execute(upsert_sql, {
                    "k": row['oda_kodu'],
                    "a": row['oda_adi'],
                    "mn": row['min_sicaklik'],
                    "mx": row['max_sicaklik'],
                    "t": row['sapma_takip_dakika'],
                    "s": row['olcum_sikligi'],
                    "qr": row['qr_token'],
                    "ak": row['aktif']
                })
        print("Sync completed successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    manual_sync_rooms()
