# EKLERISTAN QMS - SOSTS Modülü - Veritabanı Şeması

import sqlite3
import os

def init_sosts_db(db_path='ekleristan_local.db'):
    """
    SOSTS modülü için gerekli 3 ana tabloyu oluşturur.
    Mevcut schema.py içerisindeki init_db() fonksiyonu sonunda çağrılabilir.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.cursor()
        
        # TABLO 1: soguk_odalar
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS soguk_odalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oda_kodu TEXT UNIQUE NOT NULL,
            oda_adi TEXT NOT NULL,
            departman TEXT,
            min_sicaklik REAL NOT NULL DEFAULT 0.0,
            max_sicaklik REAL NOT NULL DEFAULT 4.0,
            sapma_takip_dakika INTEGER NOT NULL DEFAULT 30,
            olcum_sikligi INTEGER NOT NULL DEFAULT 2, -- saat cinsinden
            qr_token TEXT UNIQUE NOT NULL,
            qr_uretim_tarihi DATETIME,
            aktif INTEGER DEFAULT 1,
            olusturulma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # TABLO 2: sicaklik_olcumleri
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sicaklik_olcumleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oda_id INTEGER NOT NULL,
            sicaklik_degeri REAL NOT NULL,
            olcum_zamani DATETIME DEFAULT CURRENT_TIMESTAMP,
            planlanan_zaman DATETIME,
            qr_ile_girildi INTEGER DEFAULT 1,
            kaydeden_kullanici TEXT,
            sapma_var_mi INTEGER DEFAULT 0,
            sapma_aciklamasi TEXT,
            olusturulma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(oda_id) REFERENCES soguk_odalar(id)
        )
        """)
        
        # TABLO 3: olcum_plani
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS olcum_plani (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oda_id INTEGER NOT NULL,
            beklenen_zaman DATETIME NOT NULL,
            gerceklesen_olcum_id INTEGER REFERENCES sicaklik_olcumleri(id),
            durum TEXT DEFAULT 'BEKLIYOR', -- BEKLIYOR / TAMAMLANDI / GECIKTI / ATILDI
            guncelleme_zamani DATETIME,
            FOREIGN KEY(oda_id) REFERENCES soguk_odalar(id)
        )
        """)
        
        conn.commit()
        print("SOSTS tabloları başarıyla hazırlandı.")

# Entegrasyon Notu:
# schema.py dosyasındaki init_db() fonksiyonunun en sonuna 
# init_sosts_db() çağrısını ekleyin.
