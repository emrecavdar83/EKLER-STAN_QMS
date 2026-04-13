"""
Pytest ortam hazırlığı — Streamlit ve DB mock.
"""
import sys
from unittest.mock import MagicMock


def _cache_decorator(*args, **kwargs):
    """
    @st.cache_data ve @st.cache_resource için evrensel mock.
    Hem @decorator hem @decorator(ttl=60) formlarını kaldırır.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        # @st.cache_resource  ← parantezsiz kullanım
        return args[0]
    # @st.cache_resource(ttl=60)  ← parantezli kullanım
    return lambda f: f


# --- Streamlit mock (UI import'larının kırılmasını önler) ---
st_mock = MagicMock()
st_mock.session_state = {}
st_mock.cache_data = _cache_decorator
st_mock.cache_resource = _cache_decorator

sys.modules["streamlit"] = st_mock
sys.modules["extra_streamlit_components"] = MagicMock()
