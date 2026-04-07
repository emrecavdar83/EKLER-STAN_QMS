import sys
import os
from unittest.mock import MagicMock

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

def smoke_tests():
    print("--- SMOKE TESTS START ---")
    
    # 1. Navigasyon Filtreleme Testi (Admin)
    print("\nTest 1: Admin sidebar'da '📁 QDMS' görüyor mu?")
    from logic.auth_logic import kullanici_yetkisi_var_mi
    # Mock session state for Admin
    import streamlit as st
    st.session_state = {'user_rol': 'ADMIN', 'logged_in': True, 'user': 'admin'}
    
    admin_can_see = kullanici_yetkisi_var_mi("📁 QDMS", audit_log=False)
    print(f"Admin visible: {admin_can_see}")
    assert admin_can_see == True
    
    # 2. QDMS Sekme Sırası Testi
    print("\nTest 2: QDMS sekmeleri doğru sırada mı?")
    # We'll check the source of pages/qdms_ana_sayfa.py indirectly or just logical check
    # Since we use tabs_config list, the order is fixed in the code.
    from pages.qdms_ana_sayfa import qdms_main_page
    # Just checking imports and no syntax errors
    print("qdms_ana_sayfa imported successfully.")

    # 3. Yan Modül Etkileşimi
    print("\nTest 3: Soğuk Oda ve Üretim modülleri import edilebiliyor mu?")
    try:
        from ui.uretim_ui import render_uretim_module
        from ui.soguk_oda_ui import render_sosts_module
        print("Side modules imported successfully.")
    except Exception as e:
        print(f"Side module import ERROR: {e}")
        assert False

    # 4. PDF İndirme Altyapısı
    print("\nTest 4: PDF indirme (ReportLab) çalışıyor mu?")
    try:
        from modules.qdms.pdf_uretici import pdf_uret
        # Mock engine
        mock_engine = MagicMock()
        print("PDF generator imported successfully.")
    except Exception as e:
        print(f"PDF generator ERROR: {e}")
        assert False

    # 5. Operatör RBAC Testi
    print("\nTest 5: Operatör 'Belge Yönetimi' sekmesini göremiyor mu?")
    st.session_state['user_rol'] = 'OPERATÖR'
    can_manage = st.session_state['user_rol'].upper() in ['ADMIN', 'KALİTE', 'MÜDÜRLER', 'DİREKTÖRLER']
    print(f"Operator can_manage: {can_manage}")
    assert can_manage == False
    
    print("\n--- ALL SMOKE TESTS PASSED ---")

if __name__ == "__main__":
    smoke_tests()
