from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- CHECKING LOGIN USERS ---")
        
        # Check for 'RULO' in username
        sql = text("SELECT * FROM ayarlar_personel WHERE kullanici_adi LIKE '%RULO%'")
        users = conn.execute(sql).fetchall()
        
        if users:
            for u in users:
                print(f"Login User: {u.kullanici_adi}, Dept: {u.bolum}, Role: {u.rol}, DeptID: {u.departman_id if hasattr(u, 'departman_id') else 'N/A'}")
        else:
            print("❌ No login user found with 'RULO' in name.")
            
        print("\n--- CHECKING DEFAULT DEPT LOGIC ---")
        # Simulate what the app does:
        # User 'RULO PASTA' -> what is their department?
        # If bolum is 'ÜRETİM > RULO PASTA' or just 'RULO PASTA'
        
except Exception as e:
    print(e)
