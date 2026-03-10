import toml
import os
from sqlalchemy import create_engine, text

def migrate_aktif_to_integer():
    print("--- PostgreSQL 'aktif' Column Type Migration Başlıyor ---")
    try:
        # Load secrets
        secrets_path = os.path.join(os.getcwd(), '.streamlit', 'secrets.toml')
        secrets = toml.load(secrets_path)
        url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
        if url.startswith('"') and url.endswith('"'):
            url = url[1:-1]
        
        engine = create_engine(url)
        
        tablolar = [
            "lokasyonlar",
            "ayarlar_bolumler",
            "ayarlar_temizlik_plani",
            "gmp_soru_havuzu",
            "lokasyon_tipleri",
            "temizlik_dogrulama_kriterleri",
            "ayarlar_moduller"
        ]
        
        with engine.begin() as conn:
            for tablo in tablolar:
                print(f"Tablo inceleniyor: {tablo}")
                try:
                    # PostgreSQL'de BOOLEAN'dan INTEGER'a güvenli dönüşüm: 
                    # TRUE -> 1, FALSE -> 0
                    sql = f"""
                    ALTER TABLE {tablo} 
                    ALTER COLUMN aktif DROP DEFAULT,
                    ALTER COLUMN aktif SET DATA TYPE INTEGER USING (CASE WHEN aktif THEN 1 ELSE 0 END),
                    ALTER COLUMN aktif SET DEFAULT 1;
                    """
                    conn.execute(text(sql))
                    print(f"  ✅ {tablo}.aktif -> INTEGER")
                except Exception as e:
                    if "does not exist" in str(e).lower():
                        print(f"  ℹ️ {tablo} veya aktif sütunu yok, atlandı.")
                    elif "already is type integer" in str(e).lower() or "integer" in str(e).lower():
                        # Postgres error messages for types are complex, 
                        # but if it fails it might already be int.
                        print(f"  ℹ️ {tablo}.aktif zaten düzgün tipte olabilir veya hata: {e}")
                    else:
                        print(f"  ⚠️ {tablo} hatası: {e}")

        print("✅ Migration başarıyla tamamlandı.")
        
    except Exception as e:
        print(f"KRİTİK HATA: {e}")

if __name__ == "__main__":
    migrate_aktif_to_integer()
