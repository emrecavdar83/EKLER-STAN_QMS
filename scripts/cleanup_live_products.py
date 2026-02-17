import toml
import sqlalchemy
import pandas as pd
from sqlalchemy import text

def cleanup_live_products():
    # Load secrets
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = (secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")).strip('"')
    
    engine = sqlalchemy.create_engine(db_url)
    
    with engine.begin() as conn:
        print("Mevcut ürün sayısı kontrol ediliyor...")
        count_res = conn.execute(text("SELECT count(*) FROM ayarlar_urunler")).scalar()
        print(f"Başlangıçtaki toplam ürün sayısı: {count_res}")
        
        # Keep the one with the highest ID or latest creation if exists, 
        # but ayarlar_urunler usually doesn't have a reliable ID for duplicates sometimes.
        # Let's see what columns we have
        cols_res = conn.execute(text("SELECT * FROM ayarlar_urunler LIMIT 1"))
        cols = cols_res.keys()
        print(f"Sütunlar: {list(cols)}")
        
        # Standard approach: Create a temporary table with unique rows, then replace.
        # We'll use urun_adi as the uniqueness criteria.
        
        print("Mükerrer kayıtlar temizleniyor...")
        conn.execute(text("""
            CREATE TABLE ayarlar_urunler_temp AS
            SELECT DISTINCT ON (urun_adi) *
            FROM ayarlar_urunler
            ORDER BY urun_adi;
        """))
        
        conn.execute(text("TRUNCATE TABLE ayarlar_urunler;"))
        
        conn.execute(text("INSERT INTO ayarlar_urunler SELECT * FROM ayarlar_urunler_temp;"))
        
        conn.execute(text("DROP TABLE ayarlar_urunler_temp;"))
        
        final_count = conn.execute(text("SELECT count(*) FROM ayarlar_urunler")).scalar()
        print(f"Temizlik sonrası toplam ürün sayısı: {final_count}")

if __name__ == "__main__":
    cleanup_live_products()
