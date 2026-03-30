from database.connection import get_engine
from sqlalchemy import text
import sys

def fix_elvan_record():
    engine = get_engine()
    try:
        with engine.begin() as conn:
            # 1. Hatalı kaydı bul ve sil (Sadece kullanıcı adında '?' olanlar)
            # Not: Like '%?%' sqlite için bazen zorlayıcı olabilir, spesifik kelime arıyoruz
            sql_del = text("DELETE FROM personel WHERE kullanici_adi LIKE 'elvan.ozdemi%' AND kullanici_adi LIKE '%?%'")
            result = conn.execute(sql_del)
            print(f"Silinen hatalı kayıt sayısı: {result.rowcount}")
            
            # 2. Doğru kaydı bul ve rolünü BÖLÜM SORUMLUSU olarak güncelle/teyit et
            sql_upd = text("""
                UPDATE personel 
                SET rol = 'BÖLÜM SORUMLUSU', durum = 'AKTİF' 
                WHERE kullanici_adi = 'elvan.ozdemirel'
            """)
            conn.execute(sql_upd)
            print("elvan.ozdemirel kaydı BÖLÜM SORUMLUSU olarak güncellendi/mühürlendi.")
            
        print("\n✅ Elvan Özdemirel onarımı başarıyla tamamlandı.")
    except Exception as e:
        print(f"❌ Hata oluştu: {str(e)}")

if __name__ == "__main__":
    fix_elvan_record()
