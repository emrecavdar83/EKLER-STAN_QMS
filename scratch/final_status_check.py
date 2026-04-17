import sys
import os
from sqlalchemy import text

# Add workspace to path
sys.path.append(os.getcwd())

from database.connection import get_engine

def get_status():
    engine = get_engine()
    with engine.connect() as conn:
        # Check tables
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        tables = [t[0] for t in tables]
        
        print(f"AYARLAR_KULLANICILAR: {'OK' if 'ayarlar_kullanicilar' in tables else 'MISSING'}")
        print(f"PERSONEL (Legacy): {'EXISTS' if 'personel' in tables else 'REMOVED'}")
        
        if 'ayarlar_kullanicilar' in tables:
            count = conn.execute(text("SELECT count(*) FROM ayarlar_kullanicilar")).scalar()
            print(f"Records in new table: {count}")

        # Check for ADMIN role in DB vs standardized
        admin_data = conn.execute(text("SELECT rol FROM ayarlar_kullanicilar WHERE kullanici_adi = 'Admin' OR kullanici_adi = 'admin'")).fetchall()
        print(f"Admin Roles in DB: {[r[0] for r in admin_data]}")

if __name__ == "__main__":
    get_status()
