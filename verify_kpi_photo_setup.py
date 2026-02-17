
import sqlite3
import os

def verify():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # Check schema
    cursor.execute("PRAGMA table_info(Urun_KPI_Kontrol)")
    columns = [row[1] for row in cursor.fetchall()]
    if "fotograf_yolu" in columns:
        print("✅ Success: fotograf_yolu column found in local database.")
    else:
        print("❌ Error: fotograf_yolu column NOT found in local database.")
        
    # Check directory
    upload_dir = "data/uploads/kpi"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        print(f"✅ Created directory: {upload_dir}")
    else:
        print(f"✅ Directory already exists: {upload_dir}")
    
    conn.close()

if __name__ == "__main__":
    verify()
