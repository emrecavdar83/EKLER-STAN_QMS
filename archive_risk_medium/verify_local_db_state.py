import sqlite3
import pandas as pd

DB_PATH = 'ekleristan_local.db'

def verify_db():
    print(f"Connecting to {DB_PATH}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check active count
        cursor.execute("SELECT count(*) FROM personnel WHERE durum = 'AKTİF'")
        active_count = cursor.fetchone()[0]
        
        # Check total count
        cursor.execute("SELECT count(*) FROM personnel")
        total_count = cursor.fetchone()[0]
        
        print(f"Total Personnel: {total_count}")
        print(f"Active Personnel: {active_count}")
        
        # Check specific new users to see if update happened
        # 'ABDALRAOUF O A BARGHOUTH' was in the update file
        print("\nChecking for sample user 'ABDALRAOUF'...")
        cursor.execute("SELECT id, ad_soyad, durum, vardiya, servis_duragi, telefon_no FROM personnel WHERE ad_soyad LIKE '%ABDALRAOUF%'")
        user = cursor.fetchone()
        if user:
            print(f"Found: {user}")
        else:
            print("User 'ABDALRAOUF' NOT FOUND.")

        # Check for another random user from the list 'TELAL ŞAKİFA'
        print("\nChecking for sample user 'TELAL ŞAKİFA'...")
        cursor.execute("SELECT id, ad_soyad, durum, vardiya, servis_duragi, telefon_no FROM personnel WHERE ad_soyad LIKE '%TELAL%'")
        user = cursor.fetchone()
        if user:
            print(f"Found: {user}")
        else:
            print("User 'TELAL ŞAKİFA' NOT FOUND.")
            
        conn.close()
        
    except Exception as e:
        print(f"Error verifying DB: {e}")

if __name__ == "__main__":
    verify_db()
