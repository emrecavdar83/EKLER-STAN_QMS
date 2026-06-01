"""
v9.0.0: Soft Delete Geçiş Migration Dosyası.
Mevcut verileri koruyarak is_deleted kolonu ekler.
"""
from sqlalchemy import text
from database.connection import get_engine

def migrate():
    engine = get_engine()
    with engine.begin() as conn:
        # 1. personel_vardiya_programi
        conn.execute(text("""
            ALTER TABLE personel_vardiya_programi 
            ADD COLUMN IF NOT EXISTS is_deleted INTEGER DEFAULT 0
        """))
        # 2. ayarlar_kullanicilar
        conn.execute(text("""
            ALTER TABLE ayarlar_kullanicilar 
            ADD COLUMN IF NOT EXISTS is_deleted INTEGER DEFAULT 0
        """))
    print("Soft Delete Migration TAMAMLANDI.")

if __name__ == "__main__":
    migrate()
