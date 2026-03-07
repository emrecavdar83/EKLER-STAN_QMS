import toml
from sqlalchemy import create_engine, text

def migrate_add_sorumlu():
    print("--- SOGUK_ODALAR TABLOSUNA 'SORUMLU_PERSONEL' EKLENİYOR ---")

    # 1. Cloud Database (PostgreSQL)
    st_secrets = {}
    try:
        with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
            st_secrets = toml.load(f)
        
        db_url = st_secrets.get("streamlit", {}).get("DB_URL")
        if not db_url:
            db_url = st_secrets.get("database", {}).get("DB_URL")
            
        if db_url:
            print("\nCloud Veritabanı (PostgreSQL) İşleniyor...")
            engine_cloud = create_engine(db_url)
            with engine_cloud.begin() as conn:
                try:
                    conn.execute(text("ALTER TABLE soguk_odalar ADD COLUMN sorumlu_personel VARCHAR(100) DEFAULT 'Atanmadı'"))
                    print("✅ Cloud: 'sorumlu_personel' sütunu başarıyla eklendi.")
                except Exception as e:
                    print(f"⚠️ Cloud Hata (Zaten var olabilir): {e}")
        else:
            print("\nCloud Veritabanı URL'si bulunamadı, atlanıyor.")
    except Exception as e:
        print(f"\nCloud bağlantı hatası: {e}")

    # 2. Local Database (SQLite)
    print("\nLokal Veritabanı (SQLite) İşleniyor...")
    engine_local = create_engine('sqlite:///ekleristan_local.db')
    
    with engine_local.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE soguk_odalar ADD COLUMN sorumlu_personel VARCHAR(100) DEFAULT 'Atanmadı'"))
            print("✅ Lokal: 'sorumlu_personel' sütunu başarıyla eklendi.")
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                print("✅ Lokal: 'sorumlu_personel' sütunu zaten var.")
            else:
                print(f"⚠️ Lokal Hata: {e}")

    print("\n--- MİGRASYON TAMAMLANDI ---")

if __name__ == "__main__":
    migrate_add_sorumlu()
