import sqlite3
import os

def run_migration():
    print("--- v4.1.4 Naming Migration Starting (Self-Contained) ---")
    # Dinamik yol tespiti
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'ekleristan_local.db')
    
    if not os.path.exists(db_path):
        print(f"Migration Skipped: DB not found at {db_path}")
        return False
    
    # Yeni İsimler
    OLD_LABEL = "📊 Performans & Polivalans"
    NEW_LABEL = "📈 Yetkinlik & Performans"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. ayarlar_moduller
        cursor.execute("UPDATE ayarlar_moduller SET modul_etiketi = ? WHERE modul_etiketi = ? OR modul_anahtari = 'performans_polivalans'", (NEW_LABEL, OLD_LABEL))
        row1 = cursor.rowcount
        
        # 2. sistem_modulleri
        cursor.execute("UPDATE sistem_modulleri SET etiket = ? WHERE etiket = ? OR anahtar = 'performans_polivalans'", (NEW_LABEL, OLD_LABEL))
        row2 = cursor.rowcount
        
        conn.commit()
        conn.close()
        print(f"Migration Success. Rows updated: {row1 + row2}")
        return True
    except Exception as e:
        print(f"Migration Failed: {e}")
        return False

if __name__ == "__main__":
    run_migration()
