
import psycopg2
import sqlite3
import os
from datetime import datetime

DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
SQLITE_PATH = "ekleristan_local.db"

def deep_audit_v2():
    print(f"--- DEEP AUDIT V2 START (Time: {datetime.now()}) ---")
    
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
            zaman = r[0] if r[0] else "N/A"
            tip = r[1] if r[1] else "N/A"
            detay = r[2] if r[2] else "N/A"
            print(f"{zaman} | {tip:25} | {detay}")
            
        print("\n[CLOUD] Bugün Güncellenen Personeller:")
        cur.execute("""
            SELECT id, ad_soyad, rol, bolum, guncelleme_tarihi 
            FROM personel 
            WHERE guncelleme_tarihi::date = CURRENT_DATE 
            ORDER BY guncelleme_tarihi DESC
        """)
        for r in cur.fetchall():
            pid = r[0]
            ad = r[1] if r[1] else "N/A"
            rol = r[2] if r[2] else "N/A"
            bolum = r[3] if r[3] else "N/A"
            tarih = r[4] if r[4] else "N/A"
            print(f"ID: {pid} | Ad: {ad:20} | Rol: {rol:15} | Bölüm: {bolum:20} | Tarih: {tarih}")
            
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
            cur.execute("SELECT zaman, islem_tipi, detay FROM sistem_loglari ORDER BY zaman DESC LIMIT 20")
            for r in cur.fetchall():
                print(f"{r[0]} | {r[1]:25} | {r[2]}")
            conn.close()
    except Exception as e:
        print(f"Local Audit Error: {e}")

if __name__ == "__main__":
    deep_audit_v2()
