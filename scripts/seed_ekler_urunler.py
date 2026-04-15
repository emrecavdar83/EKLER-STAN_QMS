import sqlite3
import os

DB_PATH = "ekleristan_local.db"

EKLER_LIST = [
    "BITTER ÇIKOLATALI EKLER", "LOTUS EKLER", "KLASİK EKLER", "ANTEP FISTIKLI EKLER",
    "TİREMİSU EKLER", "FINDIKLI EKLER", "KİTKAT EKLER", "FRAMBUAZLI EKLER",
    "BEYAZ ÇIKOLATALI EKLER", "KARAMELLİ EKLER", "BADEMLİ EKLER", "AMBER EKLER",
    "VİŞNE EKLER", "YABAN MERSİNİ-LİMON KARMA EKLER", "ÇİLEK-BÖĞÜRTLEN KARMA EKLER",
    "MUZ-MOCHA KARMA EKLER", "KARADUT-PORTAKAL KARMA EKLER", "VİŞNE-HİNDİSTAN CEVİZİ KARMA EKLER",
    "ANANAS-KESTANE KARMA EKLER", "ELMA-İNCİR KARMA EKLER", "BÖĞÜRTLEN EKLER",
    "ÇİLEK EKLER", "BALKABAĞI-TAHİN EKLER", "YABAN MERSİNİ EKLER", "MUZ EKLER",
    "HİNDİSTAN CEVİZİ EKLER", "PORTAKAL EKLER", "MOCHA EKLER", "İNCİR-CEVİZ EKLER",
    "KESTANE EKLER", "KARADUT EKLER", "ANANAS EKLER", "ELMA-TARÇIN EKLER"
]

def run_seed():
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"--- SEED: {len(EKLER_LIST)} ADET ÜRÜN İŞLENİYOR ---")

    # Varsayılan departman bul (Üretim içeren ilk birim)
    cursor.execute("SELECT ad FROM qms_departmanlar WHERE ad LIKE '%ÜRETİM%' OR ad LIKE '%PASTANE%' OR ad LIKE '%EKLERİSTAN%' LIMIT 1")
    row = cursor.fetchone()
    default_dept = row[0] if row else "GIDA ÜRETİM"

    for urun in EKLER_LIST:
        # UPSERT (urun_adi unique constraint'ine göre)
        cursor.execute("""
            INSERT INTO ayarlar_urunler (urun_adi, urun_tipi, sorumlu_departman, raf_omru_gun, numune_sayisi, versiyon_no)
            VALUES (?, 'MAMUL', ?, 3, 3, 1)
            ON CONFLICT(urun_adi) DO UPDATE SET
                urun_tipi = excluded.urun_tipi,
                sorumlu_departman = excluded.sorumlu_departman
        """, (urun, default_dept))
    
    conn.commit()
    conn.close()
    print("SUCCESS: Seed data basarıyla yuklendi.")

if __name__ == "__main__":
    run_seed()
