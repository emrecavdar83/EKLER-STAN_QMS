import streamlit as st
from sqlalchemy import text
from database.connection import get_engine

def purge_garbage_tables():
    engine = get_engine()
    tables_to_drop = [
        "flow_definitions", "flow_nodes", "flow_edges", 
        "flow_bypass_logs", "personnel_tasks"
    ]
    
    print("🧹 [v5.8.16] Başlatılıyor: Veritabanı Temizliği...")
    
    with engine.begin() as conn:
        for tbl in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
                print(f"  ✅ Silindi: {tbl}")
            except Exception as e:
                # SQLite doesn't support CASCADE, try without it
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
                    print(f"  ✅ Silindi (No Cascade): {tbl}")
                except Exception as e2:
                    print(f"  ❌ Hata ({tbl}): {e2}")

if __name__ == "__main__":
    purge_garbage_tables()
