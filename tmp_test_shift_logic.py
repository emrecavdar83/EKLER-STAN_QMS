import sys
import os
import toml
import pandas as pd
from sqlalchemy import text
sys.path.append(os.getcwd())

from database.connection import get_engine

def test_dynamic_shift_logic():
    engine = get_engine()
    print(f"Bağlanılan Veritabanı: {engine.url}")
    
    with engine.begin() as conn:
        print("\n--- ADIM 1: Test İçin Örnek Personel Seçimi ---")
        try:
            test_personel_df = pd.read_sql(text("SELECT id, ad_soyad FROM personel WHERE durum = 'AKTİF' LIMIT 1"), conn)
            if test_personel_df.empty:
                print("❌ Aktif personel bulunamadı, test iptal ediliyor.")
                return
            
            p_id = test_personel_df.iloc[0]['id']
            p_ad = test_personel_df.iloc[0]['ad_soyad']
            print(f"Test edilecek personel: {p_ad} (ID: {p_id})")
            
            print("\n--- ADIM 2: Sahte (Test) Vardiya Kaydı Oluşturma (BUGÜN İÇİN 'GECE VARDİYASI') ---")
            
            # Eğer varsa eski çakışan kayıtları temizle
            conn.execute(text("DELETE FROM personel_vardiya_programi WHERE aciklama = 'GECİCİ_SİSTEM_TESTİ'"))
            
            # Bugünü kapsayan bir test kaydı ekle
            insert_query = text("""
                INSERT INTO personel_vardiya_programi 
                (personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri, aciklama)
                VALUES (:pid, CURRENT_DATE, CURRENT_DATE, 'GECE VARDİYASI', 'Yok', 'GECİCİ_SİSTEM_TESTİ')
            """)
            conn.execute(insert_query, {"pid": int(p_id)})
            print(f"✅ {p_ad} için sistem üzerinde sadece BUGÜNÜ kapsayan 'GECE VARDİYASI' test ataması yapıldı.")
            
            print("\n--- ADIM 3: Hijyen Modülü Dinamik Sorgu Testi ---")
            # Hijyen modülümüz personelleri nasıl görüyor test edelim:
            hijyen_query = text("""
                SELECT p.ad_soyad,
                       COALESCE(vp.vardiya, 'GÜNDÜZ VARDİYASI') as anlik_vardiya
                FROM personel p
                LEFT JOIN personel_vardiya_programi vp 
                       ON p.id = vp.personel_id 
                       AND CURRENT_DATE BETWEEN CAST(vp.baslangic_tarihi AS DATE) AND CAST(vp.bitis_tarihi AS DATE)
                WHERE p.id = :pid
            """)
            test_df = pd.read_sql(hijyen_query, conn, params={"pid": int(p_id)})
            anlik = test_df.iloc[0]['anlik_vardiya']
            
            print(f"Modülün Gördüğü Vardiya: {anlik}")
            if anlik == "GECE VARDİYASI":
                print("✅ SİSTEM BAŞARILI! Dinamik vardiya geçişi hatasız okundu. Modül personeli Gece Vardiyasında algıladı.")
            else:
                print(f"❌ KONTROL HATASI! Beklenen: GECE VARDİYASI, Okunan: {anlik}")
            
            print("\n--- ADIM 4: Temizlik (Test Verilerini Silme) ---")
            conn.execute(text("DELETE FROM personel_vardiya_programi WHERE aciklama = 'GECİCİ_SİSTEM_TESTİ'"))
            print("✅ Test verileri ('GECİCİ_SİSTEM_TESTİ' etiketli) kalıcı olarak veritabanından SİLİNDİ.")
            
            # Doğrulama: Fallback geri çalışıyor mu?
            print("\n--- ADIM 5: Doğrulama (Fallback Mekanizması) ---")
            safe_df = pd.read_sql(hijyen_query, conn, params={"pid": int(p_id)})
            eski = safe_df.iloc[0]['anlik_vardiya']
            print(f"Veri silindikten sonra modülün gördüğü vardiya: {eski}")
            if eski == "GÜNDÜZ VARDİYASI":
                print("✅ DOĞRULAMA BAŞARILI! Kayıt silinince personel sorunsuz şekilde varsayılan (Gündüz) grubuna düştü.")
            else:
                print(f"❌ KONTROL HATASI! Gündüz'e dönmesi gerekiyordu ama '{eski}' okundu.")

        except Exception as e:
            print(f"Test Hatası: {e}")

if __name__ == "__main__":
    test_dynamic_shift_logic()
