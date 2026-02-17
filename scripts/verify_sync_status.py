
import sqlite3
import pandas as pd
import os

DB_PATH = "ekleristan_local.db"

def verify_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- 📊 DATABASE VERIFICATION REPORT ---")
    
    # 1. Total Counts
    total = cursor.execute("SELECT COUNT(*) FROM personel").fetchone()[0]
    active = cursor.execute("SELECT COUNT(*) FROM personel WHERE durum = 'AKTİF'").fetchone()[0]
    deleted = cursor.execute("SELECT COUNT(*) FROM personel WHERE durum = 'PASİF'").fetchone()[0] # Assuming PASIF or deleted records remain? Script actually deletes them.
    
    # The sync script actually performs HARD DELETE on records not in master list (or keeps duplicates).
    # so we should check if any remain that shouldn't be there, but hard to know without master list in memory.
    # We will just report current counts.
    
    print(f"Total Personnel: {total}")
    print(f"Active Personnel: {active}")
    
    # 2. Manager Assignment
    with_manager = cursor.execute("SELECT COUNT(*) FROM personel WHERE yonetici_id IS NOT NULL AND yonetici_id != 0").fetchone()[0]
    print(f"Personnel with Manager Assigned: {with_manager}")
    print(f"Personnel WITHOUT Manager: {total - with_manager}")
    
    # 3. Department Breakdown
    print("\n--- 🏢 Department Breakdown (Active) ---")
    dept_stats = pd.read_sql("""
        SELECT bolum, COUNT(*) as count, 
               SUM(CASE WHEN yonetici_id IS NOT NULL AND yonetici_id != 0 THEN 1 ELSE 0 END) as managed_count
        FROM personel 
        WHERE durum = 'AKTİF'
        GROUP BY bolum
        ORDER BY count DESC
    """, conn)
    print(dept_stats.to_string(index=False))
    
    # 4. Check for Empty Critical Fields
    print("\n--- ⚠️ Missing Data Check ---")
    missing_phone = cursor.execute("SELECT COUNT(*) FROM personel WHERE telefon_no IS NULL OR telefon_no = ''").fetchone()[0]
    missing_shift = cursor.execute("SELECT COUNT(*) FROM personel WHERE vardiya IS NULL OR vardiya = ''").fetchone()[0]
    missing_service = cursor.execute("SELECT COUNT(*) FROM personel WHERE servis_duragi IS NULL OR servis_duragi = ''").fetchone()[0]
    
    print(f"Missing Phone Number: {missing_phone}")
    print(f"Missing Shift Info: {missing_shift}")
    print(f"Missing Service Info: {missing_service}")

    # 5. Check Manager Consistency
    # Check if managers exist in the personnel table
    print("\n--- 👤 Manager Validation ---")
    invalid_managers = pd.read_sql("""
        SELECT p.id, p.ad_soyad, p.yonetici_id 
        FROM personel p
        LEFT JOIN personel m ON p.yonetici_id = m.id
        WHERE p.yonetici_id IS NOT NULL AND p.yonetici_id != 0 AND m.id IS NULL
    """, conn)
    
    if not invalid_managers.empty:
        print("❌ Found personnel with invalid manager IDs (Manager not in DB):")
        print(invalid_managers)
    else:
        print("✅ All assigned manager IDs exist in the personnel table.")

    conn.close()

if __name__ == "__main__":
    verify_db()
