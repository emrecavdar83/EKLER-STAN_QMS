
import psycopg2
import sqlite3
import os

DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
SQLITE_PATH = "ekleristan_local.db"

def repair_data_integrity():
    print("--- DATA INTEGRITY REPAIR START ---")
    
    # 1. Cloud Repair (PostgreSQL)
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Departman haritasını al
        cur.execute("SELECT id, bolum_adi FROM ayarlar_bolumler")
        dept_map = {r[0]: r[1] for r in cur.fetchall()}
        
        # Personelleri güncelle (bolum metnini id'ye göre zorla)
        print("\n[CLOUD] Personel 'bolum' metinleri ID'ye göre senkronize ediliyor...")
        updated_count = 0
        for d_id, d_name in dept_map.items():
            cur.execute("""
                UPDATE personel 
                SET bolum = %s 
                WHERE departman_id = %s AND (bolum != %s OR bolum IS NULL)
            """, (d_name, d_id, d_name))
            updated_count += cur.rowcount
            
        print(f"✅ Cloud: {updated_count} personel kaydı düzeltildi.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Cloud Repair Error: {e}")

    # 2. Local Repair (SQLite)
    try:
        if os.path.exists(SQLITE_PATH):
            conn = sqlite3.connect(SQLITE_PATH)
            cur = conn.cursor()
            
            # Departman haritasını al
            cur.execute("SELECT id, bolum_adi FROM ayarlar_bolumler")
            dept_map = {r[0]: r[1] for r in cur.fetchall()}
            
            print("\n[LOCAL] Personel 'bolum' metinleri ID'ye göre senkronize ediliyor...")
            updated_count = 0
            for d_id, d_name in dept_map.items():
                cur.execute("""
                    UPDATE personel 
                    SET bolum = ? 
                    WHERE departman_id = ? AND (bolum != ? OR bolum IS NULL)
                """, (d_name, d_id, d_name))
                updated_count += cur.rowcount
            
            conn.commit()
            print(f"✅ Local: {updated_count} personel kaydı düzeltildi.")
            conn.close()
    except Exception as e:
        print(f"❌ Local Repair Error: {e}")

if __name__ == "__main__":
    repair_data_integrity()
