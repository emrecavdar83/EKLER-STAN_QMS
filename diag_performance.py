import streamlit as st
import time
from database.connection import get_engine
from sqlalchemy import text
import pandas as pd

def run_diagnostics():
    st.title("🛡️ Sistem Tanılama (Performans Analizi)")
    engine = get_engine()
    
    with st.status("Veritabanı Analiz Ediliyor...", expanded=True) as status:
        # 1. Bağlantı Testi
        t0 = time.time()
        with engine.connect() as conn:
            t1 = time.time()
            st.write(f"✅ DB Bağlantı Süresi: **{t1-t0:.3f} sn**")
            
            # 2. İndeks Kontrolü
            st.write("🔍 İndeksler Kontrol Ediliyor...")
            is_pg = engine.dialect.name == 'postgresql'
            if is_pg:
                idx_sql = """
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename IN ('map_vardiya', 'map_zaman_cizelgesi', 'map_fire_kaydi')
                """
            else:
                idx_sql = "SELECT name FROM sqlite_master WHERE type='index'"
            
            indexes = pd.read_sql(idx_sql, conn)
            st.dataframe(indexes)
            
            # 3. Tablo Boyutları
            st.write("📊 Tablo Boyutları:")
            tables = ['map_vardiya', 'map_zaman_cizelgesi', 'map_fire_kaydi', 'ayarlar_moduller']
            for t in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                st.write(f"- `{t}`: **{count} kayıt**")
                
            # 4. Kritik Sorgu Performansı
            st.write("⚡ Sorgu Performans Testi...")
            q_tests = [
                ("Aktif Vardiyalar", "SELECT * FROM map_vardiya WHERE durum='ACIK'"),
                ("Zaman Çizelgesi (Son)", "SELECT * FROM map_zaman_cizelgesi ORDER BY id DESC LIMIT 100")
            ]
            for label, q in q_tests:
                t_start = time.time()
                conn.execute(text(q)).fetchall()
                t_end = time.time()
                st.write(f"- {label}: **{t_end-t_start:.3f} sn**")
        
        status.update(label="Tanılama Tamamlandı", state="complete")

if __name__ == "__main__":
    run_diagnostics()
