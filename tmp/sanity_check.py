import sys
import os

# Mevcut çalışma dizinini PYTHONPATH'e ekle
sys.path.append(os.getcwd())

try:
    import streamlit as st
    from sqlalchemy import text
    from database.connection import get_engine
    from logic.auth_logic import kalici_oturum_olustur, kalici_oturum_dogrula, oturum_modul_guncelle
    
    print("✅ Modül importları başarılı.")
    
    engine = get_engine()
    with engine.connect() as conn:
        print("✅ Veritabanı bağlantısı başarılı.")
        
        # Sütun kontrolü
        res = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sistem_oturum_izleri'
        """)).fetchall()
        cols = [r[0] for r in res]
        
        if 'son_modul' in cols:
            print("✅ 'son_modul' sütunu mevcut.")
        else:
            print("❌ 'son_modul' sütunu eksik! Migration çalıştırılmamış.")
            
        if 'son_erisim_ts' in cols:
            print("✅ 'son_erisim_ts' sütunu mevcut.")
        else:
            print("❌ 'son_erisim_ts' sütunu eksik!")

    print("\n🚀 SİSTEM KONTROLÜ TAMAMLANDI.")

except Exception as e:
    print(f"❌ HATA TESPİT EDİLDİ: {e}")
    sys.exit(1)
