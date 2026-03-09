import sqlite3
import pandas as pd

def test_dynamic_shift_logic_sqlite():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    print("Bağlanılan Veritabanı: Lokal (SQLite)")
    
    print("\n--- ADIM 1: Test İçin Örnek Personel Seçimi ---")
    try:
        test_personel_df = pd.read_sql_query("SELECT id, ad_soyad FROM personel WHERE durum = 'AKTİF' LIMIT 1", conn)
        if test_personel_df.empty:
            print("❌ Aktif personel bulunamadı, test iptal ediliyor.")
            return
        
        p_id = test_personel_df.iloc[0]['id']
        p_ad = test_personel_df.iloc[0]['ad_soyad']
        print(f"Test edilecek personel: {p_ad} (ID: {p_id})")
        
        print("\n--- ADIM 2: Sahte (Test) Vardiya Kaydı Oluşturma (BUGÜN İÇİN 'GECE VARDİYASI') ---")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM personel_vardiya_programi WHERE aciklama = 'GECİCİ_SİSTEM_TESTİ'")
        conn.commit()
        
        # Insert test data using sqlite date functions
        insert_query = """
            INSERT INTO personel_vardiya_programi 
            (personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri, aciklama)
            VALUES (?, DATE('now', 'localtime'), DATE('now', 'localtime'), 'GECE VARDİYASI', 'Yok', 'GECİCİ_SİSTEM_TESTİ')
        """
        cursor.execute(insert_query, (int(p_id),))
        conn.commit()
        print(f"✅ {p_ad} için sistem üzerinde sadece BUGÜNÜ kapsayan 'GECE VARDİYASI' test ataması yapıldı.")
        
        print("\n--- ADIM 3: Hijyen Modülü Dinamik Sorgu Testi ---")
        hijyen_query = """
            SELECT p.ad_soyad,
                   COALESCE(vp.vardiya, 'GÜNDÜZ VARDİYASI') as anlik_vardiya
            FROM personel p
            LEFT JOIN personel_vardiya_programi vp 
                   ON p.id = vp.personel_id 
                   AND DATE('now', 'localtime') BETWEEN vp.baslangic_tarihi AND vp.bitis_tarihi
            WHERE p.id = ?
        """
        test_df = pd.read_sql_query(hijyen_query, conn, params=(int(p_id),))
        anlik = test_df.iloc[0]['anlik_vardiya']
        
        print(f"Modülün Gördüğü Vardiya: {anlik}")
        if anlik == "GECE VARDİYASI":
            print("✅ SİSTEM BAŞARILI! Dinamik vardiya geçişi hatasız okundu. Modül personeli Gece Vardiyasında algıladı.")
        else:
            print(f"❌ KONTROL HATASI! Beklenen: GECE VARDİYASI, Okunan: {anlik}")
        
        print("\n--- ADIM 4: Temizlik (Test Verilerini Silme) ---")
        cursor.execute("DELETE FROM personel_vardiya_programi WHERE aciklama = 'GECİCİ_SİSTEM_TESTİ'")
        conn.commit()
        print("✅ Test verileri ('GECİCİ_SİSTEM_TESTİ' etiketli) kalıcı olarak veritabanından SİLİNDİ.")
        
        print("\n--- ADIM 5: Doğrulama (Fallback Mekanizması) ---")
        safe_df = pd.read_sql_query(hijyen_query, conn, params=(int(p_id),))
        eski = safe_df.iloc[0]['anlik_vardiya']
        print(f"Veri silindikten sonra modülün gördüğü vardiya: {eski}")
        if eski == "GÜNDÜZ VARDİYASI":
            print("✅ DOĞRULAMA BAŞARILI! Kayıt silinince personel sorunsuz şekilde varsayılan (Gündüz) grubuna düştü.")
        else:
            print(f"❌ KONTROL HATASI! Gündüz'e dönmesi gerekiyordu ama '{eski}' okundu.")

    except Exception as e:
        print(f"Test Hatası: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_dynamic_shift_logic_sqlite()
