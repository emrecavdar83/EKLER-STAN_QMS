"""
tests/integration/conftest.py
AppTest testleri gerçek streamlit paketi gerektirir.
Üst conftest.py mock'larını bu scope'ta temizler.
"""
import sys
import importlib

# Üst conftest'in koyduğu tüm streamlit mock'larını sil
_ST_KEYS = [k for k in list(sys.modules.keys()) if k == "streamlit" or k.startswith("streamlit.")]
for _k in _ST_KEYS:
    del sys.modules[_k]

# Gerçek streamlit'i yükle
importlib.import_module("streamlit")
importlib.import_module("streamlit.testing")
importlib.import_module("streamlit.testing.v1")
