import sqlite3
import os
import shutil

def rollback():
    print("--- ACİL GERİ YÜKLEME BAŞLATILDI ---")
    
    # 1. Veritabanı Geri Yükleme
    if os.path.exists('ekleristan_local_PRE_RESTORE.db'):
        shutil.copy('ekleristan_local_PRE_RESTORE.db', 'ekleristan_local.db')
        print("✅ Veritabanı orijinal haline getirildi.")
    else:
        print("❌ HATA: Yedek veritabanı bulunamadı!")

    # 2. Klasör Yapısı Geri Yükleme
    if os.path.exists('pages_BKP'):
        if os.path.exists('pages'):
            shutil.rmtree('pages')
        os.rename('pages_BKP', 'pages')
        print("✅ 'pages' klasörü geri yüklendi.")
    
    # 3. app.py Geri Yükleme (Eğer yedek varsa)
    # Not: app.py için doğrudan bir .bak dosyası kullanmadık ama 
    # manuel olarak geri alınabilir.
    
    print("\n--- GERİ YÜKLEME TAMAMLANDI ---")
    print("Not: app.py dosyasındaki değişiklikleri manuel olarak geri almanız gerekebilir.")

if __name__ == "__main__":
    rollback()
