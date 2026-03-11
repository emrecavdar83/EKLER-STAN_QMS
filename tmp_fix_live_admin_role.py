import toml
import os
from sqlalchemy import create_engine, text

def fix_live_admin():
    print("--- Canlı DB Admin Rol Normalizasyonu Başlıyor ---")
    try:
        # Load secrets
        secrets_path = os.path.join(os.getcwd(), '.streamlit', 'secrets.toml')
        secrets = toml.load(secrets_path)
        url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
        if url.startswith('"') and url.endswith('"'):
            url = url[1:-1]
        
        engine = create_engine(url)
        
        with engine.begin() as conn:
            # 1. Personel tablosundaki Admin rollerini 'ADMIN' yap (Bypass için kritik)
            print("Personel tablosu güncelleniyor...")
            res1 = conn.execute(text("""
                UPDATE personel 
                SET rol = 'ADMIN' 
                WHERE UPPER(TRIM(rol)) = 'ADMIN' 
                   OR ad_soyad ILIKE '%ADMİN%' 
                   OR kullanici_adi ILIKE 'Admin'
            """))
            print(f"✅ {res1.rowcount} personel kaydı 'ADMIN' olarak güncellendi.")
            
            # 2. Yetki tablosundaki Admin satırlarını 'ADMIN' yap
            print("Yetki tablosu güncelleniyor...")
            res2 = conn.execute(text("""
                UPDATE ayarlar_yetkiler 
                SET rol_adi = 'ADMIN' 
                WHERE UPPER(TRIM(rol_adi)) = 'ADMIN'
            """))
            print(f"✅ {res2.rowcount} yetki kaydı 'ADMIN' olarak güncellendi.")
            
        print("🎉 Canlı veritabanı başarıyla normalize edildi.")
        
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    fix_live_admin()
