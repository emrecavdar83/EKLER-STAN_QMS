
import sqlite3

def merge_personnel():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("İşlem Başlıyor...")

        # Mevcut durumu kontrol et
        print("\n--- İŞLEM ÖNCESİ ---")
        cursor.execute("SELECT id, ad_soyad, durum, vardiya FROM personnel WHERE id IN (6, 7, 24, 25)")
        for row in cursor.fetchall():
            print(row)

        # 24 -> 6 Birleştirme
        print("\n[BİRLEŞTİRME 1] ID 24 -> ID 6'ya kopyalanıyor...")
        cursor.execute("SELECT * FROM personnel WHERE id = 24")
        rec_24 = cursor.fetchone()
        
        if rec_24:
             # ID hariç diğer alanları güncelle
             # Srtun sırası: id, ad_soyad, bolum, gorev, vardiya, durum, servis_duragi, telefon_no
             # id index 0
            query_update_6 = """
                UPDATE personnel 
                SET ad_soyad = ?, bolum = ?, gorev = ?, vardiya = ?, durum = ?, servis_duragi = ?, telefon_no = ?
                WHERE id = 6
            """
            cursor.execute(query_update_6, (rec_24[1], rec_24[2], rec_24[3], rec_24[4], rec_24[5], rec_24[6], rec_24[7]))
            print("ID 6 güncellendi.")
            
            cursor.execute("DELETE FROM personnel WHERE id = 24")
            print("ID 24 silindi.")
        else:
            print("HATA: ID 24 bulunamadı!")

        # 25 -> 7 Birleştirme
        print("\n[BİRLEŞTİRME 2] ID 25 -> ID 7'ye kopyalanıyor...")
        cursor.execute("SELECT * FROM personnel WHERE id = 25")
        rec_25 = cursor.fetchone()

        if rec_25:
            query_update_7 = """
                UPDATE personnel 
                SET ad_soyad = ?, bolum = ?, gorev = ?, vardiya = ?, durum = ?, servis_duragi = ?, telefon_no = ?
                WHERE id = 7
            """
            cursor.execute(query_update_7, (rec_25[1], rec_25[2], rec_25[3], rec_25[4], rec_25[5], rec_25[6], rec_25[7]))
            print("ID 7 güncellendi.")

            cursor.execute("DELETE FROM personnel WHERE id = 25")
            print("ID 25 silindi.")
        else:
            print("HATA: ID 25 bulunamadı!")

        conn.commit()
        print("\nDeğişiklikler kaydedildi.")

        # Son durumu kontrol et
        print("\n--- İŞLEM SONRASI ---")
        cursor.execute("SELECT id, ad_soyad, durum, vardiya FROM personnel WHERE id IN (6, 7, 24, 25)")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        
        if len(rows) == 2:
            print("\nBAŞARILI: Sadece 2 kayıt kaldı (6 ve 7).")
        else:
            print(f"\nUYARI: Beklenmeyen kayıt sayısı: {len(rows)}")

    except Exception as e:
        conn.rollback()
        print(f"\nHATA OLUŞTU, İŞLEMLER GERİ ALINDI: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    merge_personnel()
