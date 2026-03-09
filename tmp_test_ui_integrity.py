import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Streamlit context mocking (Zero-Risk Pattern)
try:
    from unittest.mock import MagicMock
    sys.modules['streamlit'] = MagicMock()
except Exception:
    pass

import streamlit as st
st.cache_resource = lambda func: func
st.cache_data = lambda *args, **kwargs: lambda func: func

# st namespace'ini mock metotlarla doldur, hata vermesin
st.subheader = lambda x: print(f"  [UI] Subheader: {x}")
st.caption = lambda x: print(f"  [UI] Caption: {x}")
st.expander = lambda x: MagicMock()

def mock_iterable(spec):
    if isinstance(spec, int): return [MagicMock() for _ in range(spec)]
    return [MagicMock() for _ in spec]

st.columns = mock_iterable
st.tabs = mock_iterable
st.container = lambda **kwargs: MagicMock()
st.markdown = lambda x: print(f"  [UI] Markdown: {x}")
st.dataframe = lambda *args, **kwargs: print("  [UI] DataFrame rendered")
st.text_input = lambda *args, **kwargs: "Mock Input"
st.selectbox = lambda *args, **kwargs: "Mock Select"
st.button = lambda *args, **kwargs: False  # Do not trigger clicks during load
st.form_submit_button = lambda *args, **kwargs: False
st.form = lambda *args, **kwargs: MagicMock()
st.data_editor = lambda df, *args, **kwargs: df

from database.connection import get_engine
from ui.ayarlar.fabrika_ui import render_lokasyon_tab, render_proses_tab
from ui.ayarlar.organizasyon_ui import render_bolum_tab, render_rol_tab

def test_ui_rendering():
    engine = get_engine()
    
    print("\n--- TEST: render_lokasyon_tab ---")
    try:
        render_lokasyon_tab(engine)
        print("✅ render_lokasyon_tab başarıyla çalıştı, çökme yok.")
    except Exception as e:
        print(f"❌ render_lokasyon_tab ÇÖKTÜ: {e}")
        raise e

    print("\n--- TEST: render_proses_tab ---")
    try:
        render_proses_tab(engine)
        print("✅ render_proses_tab başarıyla çalıştı, çökme yok.")
    except Exception as e:
        print(f"❌ render_proses_tab ÇÖKTÜ: {e}")
        raise e

    print("\n--- TEST: render_bolum_tab ---")
    try:
        render_bolum_tab(engine)
        print("✅ render_bolum_tab başarıyla çalıştı, çökme yok.")
    except Exception as e:
        print(f"❌ render_bolum_tab ÇÖKTÜ: {e}")
        raise e

    print("\n--- TEST: render_rol_tab ---")
    try:
        render_rol_tab(engine)
        print("✅ render_rol_tab başarıyla çalıştı, çökme yok.")
    except Exception as e:
        print(f"❌ render_rol_tab ÇÖKTÜ: {e}")
        raise e

if __name__ == '__main__':
    test_ui_rendering()
