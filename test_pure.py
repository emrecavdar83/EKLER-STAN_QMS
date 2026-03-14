import traceback
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime

# Bypass streamlit and reportlab before importing
import sys
from unittest.mock import MagicMock
sys.modules['streamlit'] = MagicMock()
mock_rl = MagicMock()
sys.modules['reportlab'] = mock_rl
sys.modules['reportlab.lib'] = mock_rl
sys.modules['reportlab.lib.colors'] = mock_rl
sys.modules['reportlab.lib.pagesizes'] = mock_rl
sys.modules['reportlab.lib.styles'] = mock_rl
sys.modules['reportlab.platypus'] = mock_rl
sys.modules['reportlab.lib.units'] = mock_rl

from database.connection import get_engine
from ui.map_uretim import map_db, map_rapor_pdf

def test_pure():
    try:
        # Raw engine
        engine = get_engine()
        
        with engine.connect() as conn:
            # find latest shift
            df_aktif = pd.read_sql("SELECT id, makina_no FROM map_vardiya ORDER BY id DESC LIMIT 1", conn)
            if df_aktif.empty:
                print("No shifts.")
                return
            v_id = int(df_aktif.iloc[0]['id'])
        
        print("Testing with ID:", v_id)
        html = map_rapor_pdf.uret_is_raporu_html(engine, v_id)
        
        if html:
            print("FINISHED OK, HTML length:", len(html))
        else:
            print("RETURNED NONE")
            
    except Exception as e:
        print("PYTHON CRASHED WITH:")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_pure()
