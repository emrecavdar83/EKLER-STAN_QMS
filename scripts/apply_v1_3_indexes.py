import streamlit as st
import os
import sys

# Proje kök dizinini (Root) sys.path'e ekle (ModuleNotFoundError: database hatasını önlemek için)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import get_engine

def apply_v1_3_indexes():
    """Faz 1.3 Optimizasyon İndekslerini Uygular."""
    print("🚀 Faz 1.3 Optimizasyon İndeksleri Uygulanıyor...")
    
    engine = get_engine()
    sql_file = os.path.join("migrations", "20260329_193000_optimizasyon_indeksleri.sql")
    
    if not os.path.exists(sql_file):
        print(f"❌ Hata: {sql_file} bulunamadı.")
        return

    try:
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        # UP MIGRATION kısmını al
        up_sql = sql_content.split("-- DOWN MIGRATION")[0]
        
        # Yorum satırlarını temizle (psycopg2 boş sorgu hatası vermemesi için)
        clean_lines = []
        for line in up_sql.split('\n'):
            line = line.split('--')[0].strip()
            if line:
                clean_lines.append(line)
        
        clean_sql = " ".join(clean_lines)
        commands = [cmd.strip() for cmd in clean_sql.split(";") if cmd.strip()]
        
        # PostgreSQL için AUTOCOMMIT modunda (DDL işlemleri için) bağlantı aç
        is_pg = engine.dialect.name == 'postgresql'
        maint_eng = engine.execution_options(isolation_level="AUTOCOMMIT") if is_pg else engine
        
        with maint_eng.connect() as conn:
            for cmd in commands:
                print(f"执行: {cmd[:50]}...")
                conn.execute(text(cmd))
        
        print("✅ Faz 1.3 İndeksleri Başarıyla Uygulandı.")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    # Streamlit context'i dışında çalıştığı için secrets mock-u gerekebilir 
    # Ancak biz bunu uygulama içinden veya terminalden (st.secrets varsa) çalıştıracağız.
    apply_v1_3_indexes()
