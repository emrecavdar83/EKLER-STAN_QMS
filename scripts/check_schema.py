import sys
import os

# Proje kök dizinini sys.path'e ekle (ÖNCE BU YAPILMALI)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Şimdi importlar yapılabilir
from database.connection import get_engine
from sqlalchemy import text

def check_schema():
    engine = get_engine()
    is_pg = engine.dialect.name == 'postgresql'
    
    # Connection context manager
    maint_eng = engine.execution_options(isolation_level="AUTOCOMMIT") if is_pg else engine
    
    with maint_eng.connect() as conn:
        print(f"--- Schema Check: temizlik_kayitlari (is_pg: {is_pg}) ---")
        try:
            if is_pg:
                query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'temizlik_kayitlari'")
                res = conn.execute(query).fetchall()
            else:
                query = text("PRAGMA table_info(temizlik_kayitlari)")
                res = conn.execute(query).fetchall()
                res = [(r[1],) for r in res]
                
            if not res:
                print("❌ Tablo bulunamadı!")
            else:
                for r in res:
                    print(f"Col: {r[0]}")
        except Exception as e:
            print(f"❌ Sorgulama hatası: {e}")

if __name__ == "__main__":
    check_schema()
