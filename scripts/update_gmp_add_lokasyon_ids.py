import sqlite3

# Veritabanına lokasyon_ids sütunu ekle
conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

try:
    # Yeni sütun ekle (eğer yoksa)
    cursor.execute("""
        ALTER TABLE gmp_soru_havuzu 
        ADD COLUMN lokasyon_ids TEXT DEFAULT NULL
    """)
    conn.commit()
    print("✅ lokasyon_ids sütunu başarıyla eklendi!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ Sütun zaten mevcut, güncelleme gerekmiyor.")
    else:
        print(f"❌ Hata: {e}")
finally:
    conn.close()
    
print("\n📝 Açıklama:")
print("- NULL/Boş = Tüm lokasyonlarda sorulur")
print("- '1,2,3' = Sadece ID'si 1, 2, 3 olan lokasyonlarda sorulur")
