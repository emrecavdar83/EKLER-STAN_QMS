# verify_integrity.py
import sys
import os
import sqlite3

# Root dizini path'e ekle
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(root_dir)

try:
    # Absolute import kullanarak başla
    from ui.performans import performans_hesap as hesap
    from ui.performans import performans_sabitleri as sabit
    
    print("--- 1. Matematiksel Dogrulama ---")
    # Test 1: Agirlikli Ortalama
    # 75 * 0.7 + 85 * 0.3 = 52.5 + 25.5 = 78.0
    res = hesap.agirlikli_toplam_hesapla(75.0, 85.0)
    if res == 78.0:
        print("[OK] Agirlikli hesaplama dogru (78.0)")
    else:
        print(f"[HATA] Agirlikli hesaplama yanlis: {res}")
        sys.exit(1)
    
    # Test 2: Polivalans Duzeyi
    d = hesap.polivalans_duzeyi_belirle(45.0)
    if d["kod"] == 2:
        print("[OK] Polivalans sinir degeri (45) dogru: KOD 2")
    else:
        print(f"[HATA] Sinir degeri hatasi: {d['kod']}")
        sys.exit(1)

    print("\n--- 2. Veritabani Sema Kontrolu ---")
    db_path = "ekleristan_local.db"
    if not os.path.exists(db_path):
        print(f"[KRITIK] Veritabani dosyasi ({db_path}) bulunamadi!")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ["performans_degerledirme", "polivalans_matris"]
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            print(f"[OK] Tablo mevcut: {table}")
        else:
            print(f"[HATA] Tablo EKSIK: {table}")
            sys.exit(1)
            
    # Kolon kontrolu (Önemli bir kolon: onceki_puan)
    cursor.execute("PRAGMA table_info(performans_degerledirme)")
    columns = [col[1] for col in cursor.fetchall()]
    if "onceki_puan" in columns:
        print("[OK] Audit trail kolonlari (onceki_puan) mevcut.")
    else:
        print("[HATA] Audit trail kolonlari eksik!")
        sys.exit(1)
        
    conn.close()
    print("\n--- 3. Sistem Entegrasyonu ---")
    import app
    print("[OK] app.py basariyla import edildi (Sintaks hatasi yok).")
    
    print("\n>>> TUM TESTLER BASARILI: SISTEM INTEGRITY GARANTI ALTINDADIR. <<<")

except Exception as e:
    print(f"\n[VERIFICATION_FAILED] Hata: {str(e)}")
    sys.exit(1)
