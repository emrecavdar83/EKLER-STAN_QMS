import sqlite3
import os

DB_PATH = "ekleristan_local.db"

def add_column_safe(cursor, table_name, column_name, column_type, default_val=None):
    try:
        # Prama kullanarak kolon var mı kontrol et
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        if column_name not in columns:
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_val is not None:
                if isinstance(default_val, str):
                    query += f" DEFAULT '{default_val}'"
                else:
                    query += f" DEFAULT {default_val}"
            cursor.execute(query)
            print(f"✅ {table_name} tablosuna '{column_name}' kolonu eklendi.")
        else:
            print(f"ℹ️ {table_name} tablosunda '{column_name}' kolonu zaten mevcut.")
    except Exception as e:
        print(f"❌ '{column_name}' eklenirken hata: {e}")

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Veritabanı bulunamadı: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- ÜRÜN KARTLARI MIGRATION (BRC/IFS) ---")

    # 1. ayarlar_urunler tablosunu güncelle
    add_column_safe(cursor, "ayarlar_urunler", "alerjen_bilgisi", "TEXT")
    add_column_safe(cursor, "ayarlar_urunler", "depolama_sartlari", "TEXT")
    add_column_safe(cursor, "ayarlar_urunler", "ambalaj_tipi", "TEXT")
    add_column_safe(cursor, "ayarlar_urunler", "hedef_kitle", "TEXT")
    add_column_safe(cursor, "ayarlar_urunler", "versiyon_no", "INTEGER", default_val=1)

    # 2. urun_parametreleri tablosunu güncelle
    add_column_safe(cursor, "urun_parametreleri", "birim", "TEXT")

    conn.commit()
    conn.close()
    print("--- MIGRATION BAŞARIYLA TAMAMLANDI ---")

if __name__ == "__main__":
    run_migration()
