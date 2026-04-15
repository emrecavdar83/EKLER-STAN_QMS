import sys
import os
from sqlalchemy import text

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

def verify_rls():
    from database.connection import get_engine
    engine = get_engine()
    
    with engine.connect() as conn:
        print("--- RLS DURUM RAPORU ---")
        sql = text("SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        res = conn.execute(sql).fetchall()
        
        all_ok = True
        for row in res:
            status = "✅ AKTIF" if row[1] else "❌ DEVRE DISI"
            if not row[1]: all_ok = False
            print(f"- {row[0]:<30} : {status}")
            
        if all_ok:
            print("\n🎉 TÜM TABLOLAR GÜVENLİ (RLS Aktif)")
        else:
            print("\n⚠️ EKSİK RLS TANIMLAMALARI VAR!")

if __name__ == "__main__":
    verify_rls()
