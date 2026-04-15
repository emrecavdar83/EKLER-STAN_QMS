import sys
import os
from sqlalchemy import text

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

def test_constants_db_read():
    print("Constants DB-Read Testi Baslatiliyor...")
    
    try:
        from constants import get_position_levels, get_vardiya_listesi
        from database.connection import get_engine
        
        # 1. DB'ye bağlan ve değerleri kontrol et
        engine = get_engine()
        with engine.connect() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM sistem_parametreleri")).fetchone()
            print(f"Veritabanindaki Parametre Sayisi: {res[0]}")
            
        # 2. constants.py üzerinden verileri çek (Cache devrede olabilir)
        pos = get_position_levels()
        vardiya = get_vardiya_listesi()
        
        print(f"Pozisyon Seviyeleri Sayisi: {len(pos)}")
        print(f"Vardiya Listesi: {vardiya}")
        
        if len(pos) > 0 and len(vardiya) > 0:
            print("\n🎉 TEST BAŞARILI: Sabitler veritabanından veya yedek sisteminden başarıyla yüklendi.")
        else:
            print("\n❌ TEST BAŞARISIZ: Veriler boş döndü.")
            
    except Exception as e:
        print(f"\n❌ TEST HATASI: {e}")

if __name__ == "__main__":
    test_constants_db_read()
