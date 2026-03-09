# tests/system_integrity_check.py
import sys
import os
from unittest.mock import MagicMock

# 1. Mock Streamlit completely before any imports
st = MagicMock()
st.secrets = {"DB_URL": "sqlite:///ekleristan_local.db"}
st.cache_resource = lambda f: f
st.cache_data = lambda **kwargs: lambda f: f
st.session_state = {}
sys.modules["streamlit"] = st

# 2. Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_modules():
    print("--- 🛡️ Sistem Bütünlük Kontrolü Başlatılıyor ---")
    
    modules_to_test = [
        ("Database Connection", "database.connection"),
        ("Auth Logic", "logic.auth_logic"),
        ("Smart Flow Logic", "logic.flow_manager"),
        ("SOSTS (Cold Room) UI", "ui.soguk_oda_ui"),
        ("Production UI", "ui.uretim_ui"),
        ("KPI UI", "ui.kpi_ui"),
        ("Hygiene UI", "ui.hijyen_ui"),
        ("Cleaning UI", "ui.temizlik_ui"),
        ("Reporting UI", "ui.raporlama_ui"),
        ("Settings Orchestrator", "ui.ayarlar.ayarlar_orchestrator"),
        ("Flow Designer UI", "ui.ayarlar.flow_designer_ui")
    ]
    
    success_count = 0
    for name, mod_path in modules_to_test:
        try:
            print(f"Testing {name:25} ({mod_path:35})...", end=" ")
            # Clear if already loaded (unlikely in this script but safer)
            if mod_path in sys.modules:
                del sys.modules[mod_path]
            __import__(mod_path)
            print("✅ OK")
            success_count += 1
        except Exception as e:
            print(f"❌ FAILED: {str(e)[:100]}")
            
    print(f"\n--- 📊 Özet: {success_count}/{len(modules_to_test)} Modül Sağlıklı ---")
    return success_count == len(modules_to_test)

if __name__ == "__main__":
    if check_modules():
        print("🎉 TÜM SİSTEM SAĞLIKLI ÇALIŞIYOR.")
        sys.exit(0)
    else:
        print("🛑 SİSTEMDE UYUMSUZLUK TESPİT EDİLDİ.")
        sys.exit(1)
