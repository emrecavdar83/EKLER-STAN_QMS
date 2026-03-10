
import psycopg2
import sqlite3
from datetime import datetime

DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
SQLITE_PATH = "ekleristan_local.db"

def deep_audit():
    print(f"--- DEEP AUDIT START (Time: {datetime.now()}) ---")
    
    # 1. Cloud Logs (PostgreSQL)
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("\n[CLOUD] Son 50 Sistem Logu (Bugün):")
        cur.execute("""
            SELECT zaman, islem_tipi, detay 
            FROM sistem_loglari 
            WHERE zaman::date = CURRENT_DATE 
            ORDER BY zaman DESC LIMIT 50
        """)
        for r in cur.fetchall():
            print(f"{r[0]} | {r[1]:25} | {r[2]}")
            
        print("\n[CLOUD] Bugün Güncellenen Personeller (Öğleden Sonra):")
        cur.execute("""
            SELECT id, ad_soyad, rol, bolum, guncelleme_tarihi 
            FROM personel 
            WHERE guncelleme_tarihi::date = CURRENT_DATE 
            ORDER BY guncelleme_tarihi DESC
        """)
        for r in cur.fetchall():
            print(f"ID: {r[0]} | Ad: {r[1]:20} | Rol: {r[2]:15} | Bölüm: {r[3]:20} | Tarih: {r[4]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Cloud Audit Error: {e}")

    # 2. Local Logs (SQLite)
    try:
        if os.path.exists(SQLITE_PATH):
            conn = sqlite3.connect(SQLITE_PATH)
            cur = conn.cursor()
            print("\n[LOCAL] Son 20 Sistem Logu:")
            # sqlite zaman damgası kontrolü
            cur.execute("SELECT zaman, islem_tipi, detay FROM sistem_loglari ORDER BY zaman DESC LIMIT 20")
            for r in cur.fetchall():
                print(f"{r[0]} | {r[1]:25} | {r[2]}")
            conn.close()
    except Exception as e:
        print(f"Local Audit Error: {e}")

if __name__ == "__main__":
    import os
    deep_audit()
