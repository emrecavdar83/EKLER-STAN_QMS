import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_engine
from sqlalchemy import text

def check_schema():
    engine = get_engine()
    is_pg = engine.dialect.name == 'postgresql'
    
    with engine.connect() as conn:
        print(f"--- Schema Check: ayarlar_temizlik_plani (is_pg: {is_pg}) ---")
        if is_pg:
            query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'ayarlar_temizlik_plani'")
            res = conn.execute(query).fetchall()
        else:
            query = text("PRAGMA table_info(ayarlar_temizlik_plani)")
            res = conn.execute(query).fetchall()
            res = [(r[1],) for r in res]
            
        if not res:
            print("❌ Tablo bulunamadı!")
        else:
            for r in res:
                print(f"Col: {r[0]}")

if __name__ == "__main__":
    check_schema()
