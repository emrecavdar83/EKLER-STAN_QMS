# -*- coding: utf-8 -*-
"""
Üretim Girişi - Gelişmiş Test
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('ekleristan_local.db')
cur = conn.cursor()

# Kolon bilgilerini al
cur.execute("PRAGMA table_info(depo_giris_kayitlari)")
columns = cur.fetchall()
print("📊 Tablo Yapısı:")
for col in columns:
    print(f"  [{col[0]}] {col[1]:20} ({col[2]})")

# Test verisi
test_kayit = {
    'tarih': '2026-02-07',
    'saat': '13:00',
    'vardiya': 'GÜNDÜZ VARDİYASI',
    'kullanici': 'test_user',
    'islem_tipi': 'URETIM',
    'urun': 'TEST ÜRÜN',
    'lot_no': 'LOT-TEST-001',
    'miktar': 100.0,
    'fire': 5.0,
    'notlar': 'Test: Çok satırlı not.\nSatır 2: Fire nedeni.\nSatır 3: Detay.',
    'zaman_damgasi': str(datetime.now())
}

try:
    # Kaydet
    cur.execute("""
        INSERT INTO depo_giris_kayitlari 
        (tarih, saat, vardiya, kullanici, islem_tipi, urun, lot_no, miktar, fire, notlar, zaman_damgasi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_kayit['tarih'], test_kayit['saat'], test_kayit['vardiya'],
        test_kayit['kullanici'], test_kayit['islem_tipi'], test_kayit['urun'],
        test_kayit['lot_no'], test_kayit['miktar'], test_kayit['fire'],
        test_kayit['notlar'], test_kayit['zaman_damgasi']
    ))
    conn.commit()
    print("\n✅ Test kaydı eklendi!")
    
    # Doğrulama
    cur.execute("""
        SELECT id, tarih, saat, vardiya, urun, lot_no, miktar, fire, notlar 
        FROM depo_giris_kayitlari 
        WHERE lot_no = 'LOT-TEST-001'
    """)
    row = cur.fetchone()
    
    print(f"\n📋 Kaydedilen Veri:")
    print(f"  ID: {row[0]}")
    print(f"  Tarih: {row[1]}")
    print(f"  SAAT: {row[2]} ⏰")  # ÖNEMLİ
    print(f"  Vardiya: {row[3]}")
    print(f"  Ürün: {row[4]}")
    print(f"  Lot: {row[5]}")
    print(f"  Miktar: {row[6]}")
    print(f"  Fire: {row[7]}")
    print(f"  Notlar:\n    {row[8].replace(chr(10), chr(10) + '    ')}")
    
    # Temizle
    cur.execute("DELETE FROM depo_giris_kayitlari WHERE lot_no = 'LOT-TEST-001'")
    conn.commit()
    print("\n🧹 Test kaydı silindi.")
    
except Exception as e:
    print(f"❌ Hata: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

print("\n✅ Veritabanı testi başarılı!")
