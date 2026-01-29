import os
from sqlalchemy import create_engine, text
import sys

# Basit TOML parser (sadece DB_URL için)
def get_db_url():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "DB_URL" in line:
                        # DB_URL = "..." formatını parse et
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip('"').strip("'")
        except Exception as e:
            print(f"Secrets okuma hatası: {e}")
    return None

def main():
    print("Canlı veritabanı View güncellemesi başlatılıyor...")
    
    db_url = get_db_url()
    if not db_url:
        print("HATA: .streamlit/secrets.toml dosyasında DB_URL bulunamadı veya dosya yok.")
        print("Lokal SQLite veritabanı kontrol ediliyor...")
        db_url = "sqlite:///ekleristan_local.db"
    
    print(f"Bağlanılan DB: {db_url.split('@')[-1] if '@' in db_url else 'SQLite Local'}")
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # View SQL'i
            sql = """
            CREATE OR REPLACE VIEW v_organizasyon_semasi AS
            SELECT 
                p.id,
                p.ad_soyad,
                p.gorev,
                p.rol,
                p.pozisyon_seviye,
                p.yonetici_id,
                y.ad_soyad as yonetici_adi,
                d.bolum_adi as departman,
                d.id as departman_id,
                p.kullanici_adi,
                p.durum,
                p.vardiya,
                CASE 
                    WHEN p.yonetici_id IS NULL THEN p.ad_soyad
                    ELSE y.ad_soyad || ' > ' || p.ad_soyad
                END as hiyerarsi_yolu
            FROM personel p
            LEFT JOIN personel y ON p.yonetici_id = y.id
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
            WHERE p.ad_soyad IS NOT NULL AND p.durum = 'AKTİF'
            ORDER BY p.pozisyon_seviye, d.sira_no, p.ad_soyad;
            """
            
            # SQLite için farklı syntax gerekebilir ("OR REPLACE" çalışmaz)
            if "sqlite" in db_url:
                print("SQLite algılandı, View silinip tekrar oluşturuluyor...")
                conn.execute(text("DROP VIEW IF EXISTS v_organizasyon_semasi"))
                sql = sql.replace("CREATE OR REPLACE VIEW", "CREATE VIEW")
            
            conn.execute(text(sql))
            conn.commit()
            print("BAŞARILI: v_organizasyon_semasi güncellendi (Filtre: durum='AKTİF')")
            
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    main()
