# verify_logic.py
import sys
import os

# ui/performans dizinine taşındığı için import yolunu güncelle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'ui', 'performans')))

try:
    import performans_hesap as hesap
    
    # Test 1: Ağırlıklı Ortalama
    # 75 * 0.7 + 85 * 0.3 = 52.5 + 25.5 = 78.0
    res = hesap.agirlikli_toplam_hesapla(75.0, 85.0)
    assert res == 78.0, f"Ağırlıklı hesap hatası: {res}"
    
    # Test 2: Polivalans Düzeyi
    # 45 tam sınır (Kod 2 olmalı)
    d = hesap.polivalans_duzeyi_belirle(45.0)
    assert d["kod"] == 2, f"Sınır değer hatası (45): {d['kod']}"
    
    # 44.9 (Kod 1 olmalı)
    d2 = hesap.polivalans_duzeyi_belirle(44.9)
    assert d2["kod"] == 1, f"Sınır değer hatası (44.9): {d2['kod']}"
    
    print("✅ Matematiksel Doğrulama: BAŞARILI")
    
    # Test 3: DB Integration Check (Structural)
    import sqlite3
    conn = sqlite3.connect("ekleristan_local.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='performans_degerledirme'")
    if cursor.fetchone():
        print("✅ Veritabanı Şeması: BAŞARILI")
    else:
        print("❌ Veritabanı Şeması: TABLO BULUNAMADI")
    conn.close()

except Exception as e:
    print(f"❌ Doğrulama Hatası: {e}")
    sys.exit(1)
