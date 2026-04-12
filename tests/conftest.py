"""
Test ortamı için streamlit mock'u.
database/connection.py st.cache_resource ve st.secrets kullandığı için
testlerde gerçek streamlit gerekmez — bu dosya onu taklit eder.
"""
import sys
import types
from unittest.mock import MagicMock

# Streamlit mock: sadece testlerin ihtiyacı olan kısımlar
_st_mock = types.ModuleType("streamlit")

# cache_resource: passthrough decorator (önbelleksiz, doğrudan çalışır)
def _cache_resource(func):
    return func

_st_mock.cache_resource = _cache_resource

# secrets: boş dict — connection.py SQLite fallback'e geçer
_st_mock.secrets = {}

# Diğer olası çağrılar için genel mock
_st_mock.error = MagicMock()
_st_mock.warning = MagicMock()

sys.modules["streamlit"] = _st_mock
