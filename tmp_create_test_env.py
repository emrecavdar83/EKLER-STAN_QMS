import sys
import os
from sqlalchemy import text
import time

sys.path.append(os.getcwd())
from database.connection import get_engine

def create_test_environment():
    engine = get_engine()
    with engine.connect() as conn:
        try:
            print("1. 'TEST_BOLUM' Departmanı oluşturuluyor...")
            bolum_res = conn.execute(text("SELECT id FROM ayarlar_bolumler WHERE bolum_adi = 'TEST_BOLUM'")).fetchone()
            if not bolum_res:
                conn.execute(text("INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no) VALUES ('TEST_BOLUM', 1, 999)"))
                bolum_id = conn.execute(text("SELECT id FROM ayarlar_bolumler WHERE bolum_adi = 'TEST_BOLUM'")).fetchone()[0]
                print(f"Departman oluşturuldu (ID: {bolum_id})")
            else:
                bolum_id = bolum_res[0]
                print(f"Departman zaten var (ID: {bolum_id})")

            print("2. 'TEST_ROLU' Rolü oluşturuluyor...")
            rol_res = conn.execute(text("SELECT id FROM ayarlar_roller WHERE rol_adi = 'TEST_ROLU'")).fetchone()
            if not rol_res:
                conn.execute(text("INSERT INTO ayarlar_roller (rol_adi, aciklama, aktif) VALUES ('TEST_ROLU', 'Hardcode geçişi test rölü', 1)"))
                print("Rol oluşturuldu.")
            else:
                print("Rol zaten var.")

            print("3. 'TEST_KULLANICI' Kullanıcısı oluşturuluyor...")
            usr_res = conn.execute(text("SELECT id FROM personel WHERE kullanici_adi = 'test_kullanici'")).fetchone()
            if not usr_res:
                conn.execute(text("""
                    INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, departman_id, durum, vardiya) 
                    VALUES ('TEST KULLANICISI', 'test_kullanici', 'test1234', 'TEST_ROLU', :b_id, 'AKTİF', 'GÜNDÜZ VARDİYASI')
                """), {"b_id": bolum_id})
                print("Kullanıcı oluşturuldu.")
            else:
                print("Kullanıcı zaten var.")
                
            print("4. TEST_ROLU İçin Deneme Yetkileri Atanıyor...")
            conn.execute(text("DELETE FROM ayarlar_yetkiler WHERE rol_adi = 'TEST_ROLU'"))
            
            test_yetkiler = [
                ("uretim_girisi", "Düzenle", True), 
                ("soguk_oda", "Görüntüle", False),
                ("kurumsal_raporlama", "Düzenle", False)
            ]
            for key, erisim, sinirli in test_yetkiler:
                conn.execute(text("""
                    INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu, sadece_kendi_bolumu)
                    VALUES ('TEST_ROLU', :m, :e, :s)
                """), {"m": key, "e": erisim, "s": sinirli})
                print(f"Yetki atandı: {key} -> {erisim} (Sınırlı: {sinirli})")
                
            conn.commit()
            print("\n✅ İzole Test Ortamı (Karantina) Hazır.")
        except Exception as e:
            print(f"HATA OLUŞTU: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    create_test_environment()
