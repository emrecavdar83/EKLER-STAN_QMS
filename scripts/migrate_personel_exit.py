import sqlite3
import datetime

def migrate_personel_exit():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Personel Tablosu Guncellemesi (Isten Cikis) ---")
    
    # Mevcut kolonlari kontrol et
    cursor.execute("PRAGMA table_info(personel)")
    cols = [col[1] for col in cursor.fetchall()]
    
    # Yeni kolonlar
    if 'is_cikis_tarihi' not in cols:
        print("-> is_cikis_tarihi ekleniyor...")
        cursor.execute("ALTER TABLE personel ADD COLUMN is_cikis_tarihi TEXT")
    else:
        print("-> is_cikis_tarihi zaten var.")
        
    if 'ayrilma_sebebi' not in cols:
        print("-> ayrilma_sebebi ekleniyor...")
        cursor.execute("ALTER TABLE personel ADD COLUMN ayrilma_sebebi TEXT")
    else:
        print("-> ayrilma_sebebi zaten var.")

    # Mevcut verileri standardize et (Durumu boş olanları AKTİF yap)
    print("-> Durum bilgisi standardize ediliyor (Bos -> AKTIF)...")
    cursor.execute("UPDATE personel SET durum = 'AKTİF' WHERE durum IS NULL OR durum = ''")
    
    # Değişiklikleri kaydet
    conn.commit()
    conn.close()
    
    print("--- Guncelleme TAMAMLANDI ---")

if __name__ == "__main__":
    migrate_personel_exit()
