import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from logic.sosts_bakim import sosts_bakim_calistir
from logic.alerts_logic import get_gecikme_uyarilari

def test_alerts_logic_bakim_cagirmiyor():
    """get_gecikme_uyarilari() içinde plan_uret veya kontrol_geciken_olcumler çağrılmamalı."""
    engine = MagicMock()
    with patch("soguk_oda_utils.plan_uret") as mock_plan, \
         patch("soguk_oda_utils.kontrol_geciken_olcumler") as mock_kontrol, \
         patch("streamlit.session_state", {"sosts_last_maintenance": 0}):
        
        # Test çağrısı
        get_gecikme_uyarilari(engine)
        
        # Doğrulama: Bu fonksiyonlar asla çağrılmamalı (artık manuel)
        mock_plan.assert_not_called()
        mock_kontrol.assert_not_called()

def test_bakim_audit_log_atiyor():
    """sosts_bakim_calistir() sonrası audit_log tablosunda kayıt olmalı."""
    engine = MagicMock()
    # Patch where used in sosts_bakim
    with patch("logic.sosts_bakim.audit_log_kaydet") as mock_audit, \
         patch("soguk_oda_utils.plan_uret"), \
         patch("soguk_oda_utils.kontrol_geciken_olcumler"), \
         patch("logic.sosts_bakim._son_bakim_guncelle"), \
         patch("streamlit.session_state", {}):
        
        res = sosts_bakim_calistir(engine, "test_user")
        
        if not res['basarili']:
            print(f"MAINTENANCE ERROR: {res.get('hata')}")
        assert res['basarili'] is True
        # Verify call using keyword or partial match to avoid Windows character mangling in tests
        args, kwargs = mock_audit.call_args_list[0]
        assert args[0] == "SOSTS_BAKIM"
        assert "SOSTS" in args[1]
        assert args[2] == "test_user"
