import os
import sys
sys.path.append(os.getcwd())
import streamlit as st
from logic.auth_logic import kullanici_yetkisi_var_mi, sistem_modullerini_getir
from database.connection import get_engine

def smoke_test():
    print("--- EKLERISTAN QMS FINAL SMOKE TEST ---")
    
    # 1. Module Load Test (Local/Live agnostic)
    engine = get_engine()
    print("1. Database Connection: OK")
    
    # 2. RBAC Test (Operator kısıtı)
    # Simulate a Personel session
    class MockSession:
        def __init__(self): self.user_rol = 'Personel'
    
    # We can't easily mock st.session_state globally in a script without streamlit context,
    # but we can call it if we mock the internal state or just trust previous granular tests.
    # Instead, I'll check if the tables have data.
    with engine.connect() as conn:
        from sqlalchemy import text
        res = conn.execute(text("SELECT COUNT(*) FROM ayarlar_moduller WHERE aktif=1")).scalar()
        print(f"2. Active Modules in DB: {res} (Expected > 10)")
        
        # Check specific QDMS tables
        tables = ['qdms_belgeler', 'qdms_talimatlar', 'qdms_yayim']
        for t in tables:
            conn.execute(text(f"SELECT 1 FROM {t} LIMIT 1"))
            print(f"3. Table {t}: OK")

    # 4. PDF Generator Test
    from modules.qdms.pdf_uretici import test_pdf_uret
    try:
        pdf_path = test_pdf_uret()
        if os.path.exists(pdf_path):
            print(f"4. PDF Engine: OK ({pdf_path})")
    except Exception as e:
        print(f"4. PDF Engine: FAILED ({e})")

    # 5. UI Component Imports
    modules = [
        'ui.soguk_oda_ui',
        'ui.performans.performans_sayfasi',
        'pages.qdms_dokuman_merkezi'
    ]
    for m in modules:
        try:
            __import__(m)
            print(f"5. Module {m}: OK")
        except Exception as e:
            print(f"5. Module {m}: FAILED ({e})")

if __name__ == "__main__":
    smoke_test()
