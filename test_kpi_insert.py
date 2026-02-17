from sqlalchemy import create_engine, text
from datetime import datetime

# Connect to the database
db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

def test_kpi_insert():
    print("--- KPI Kayıt Testi Başlıyor ---")
    try:
        with engine.connect() as conn:
            # Data packet similar to what the app sends
            # 20 elemanlı liste
            # [tarih, saat, vardiya, urun, "", lot_no, stt, numune_adet, avg1, avg2, avg3, karar, kullanici, simdi, "", "", tat, goruntu, not, foto]
            
            test_data = {
                "t": "2026-02-17",
                "sa": "10:30",
                "v": "TEST VARDİYASI",
                "u": "TEST ÜRÜNÜ",
                "l": "TEST-LOT-001",
                "stt": "2026-03-01",
                "num": "5",
                "o1": 10.5,
                "o2": 20.0,
                "o3": 0.0,
                "karar": "ONAY",
                "kul": "OTOMATİK_TEST_BOTU",
                "tat": "Uygun",
                "gor": "Uygun",
                "notlar": "Otomatik sistem testi",
                "foto": "test_gorsel.jpg"
            }

            sql = """INSERT INTO urun_kpi_kontrol (tarih, saat, vardiya, urun, lot_no, stt, numune_no, olcum1, olcum2, olcum3, karar, kullanici, tat, goruntu, notlar, fotograf_yolu)
                     VALUES (:t, :sa, :v, :u, :l, :stt, :num, :o1, :o2, :o3, :karar, :kul, :tat, :gor, :notlar, :foto)"""
            
            conn.execute(text(sql), test_data)
            conn.commit()
            print("✅ Kayıt veritabanına başarıyla eklendi.")
            
            # Verify insertion
            result = conn.execute(text("SELECT * FROM urun_kpi_kontrol WHERE kullanici = 'OTOMATİK_TEST_BOTU' ORDER BY id DESC LIMIT 1")).fetchone()
            if result:
                print(f"✅ Doğrulama Başarılı! ID: {result[0]}, Ürün: {result[4]}")
                
                # Cleanup
                conn.execute(text("DELETE FROM urun_kpi_kontrol WHERE kullanici = 'OTOMATİK_TEST_BOTU'"))
                conn.commit()
                print("🧹 Test verisi temizlendi.")
            else:
                print("❌ Kayıt doğrulanamadı!")

    except Exception as e:
        print(f"❌ Test Hatası: {e}")

if __name__ == "__main__":
    test_kpi_insert()
