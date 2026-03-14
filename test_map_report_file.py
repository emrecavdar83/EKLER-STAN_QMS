import os, traceback

# Monkey-patch streamlit just in case
import streamlit as st
def mock_write(*args, **kwargs): pass
st.write = mock_write
st.sidebar = type('Mock', (), {'header': mock_write, 'write': mock_write})

from database.connection import get_engine
from ui.map_uretim import map_db, map_rapor_pdf

def test_rapor():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            son_vardiya = map_db.get_son_kapatilan_vardiya(engine)
            if not son_vardiya:
                df_aktif = map_db.get_tum_aktif_vardiyalar(engine)
                if not df_aktif.empty:
                    son_vardiya = df_aktif.iloc[-1].to_dict()
            if not son_vardiya:
                with open("error_log.txt", "w", encoding="utf-8") as f:
                    f.write("Hiç vardiya yok.")
                return

        v_id = int(son_vardiya['id'])
        
        related = map_db.get_related_vardiya_ids(engine, v_id)
        
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(f"Vardiya ID: {v_id}\\n")
            f.write(f"Birlikte Raporlanacak Makineler: {related}\\n")
            
        html = map_rapor_pdf.uret_is_raporu_html(engine, v_id)
        
        with open("error_log.txt", "a", encoding="utf-8") as f:
            if html:
                f.write("\\nHTML BAŞARIYLA OLUŞTU.\\n")
            else:
                f.write("\\nHTML BOŞ DÖNDÜ.\\n")

    except Exception as e:
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write("\\nCRASH:\\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    test_rapor()
