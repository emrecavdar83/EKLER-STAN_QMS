from app import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        print("SİSTEM ADMIN temizleniyor...")
        result = conn.execute(text("DELETE FROM personel WHERE kullanici_adi = 'Admin'"))
        conn.commit()
        print(f"Silinen kayıt sayısı: {result.rowcount}")
        
        # Kontrol
        res = conn.execute(text("SELECT COUNT(*) FROM personel WHERE kullanici_adi = 'Admin'")).fetchone()
        if res[0] == 0:
            print("✅ SİSTEM ADMIN başarıyla ve kalıcı olarak silindi.")
        else:
            print("❌ Silme başarısız oldu!")

except Exception as e:
    print(f"Hata: {e}")
