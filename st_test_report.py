import streamlit as st
import traceback
from database.connection import get_engine
from ui.map_uretim import map_db, map_rapor_pdf

def main():
    st.write("## Test MAP Report")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            son_vardiya = map_db.get_son_kapatilan_vardiya(engine)
            if not son_vardiya:
                df_aktif = map_db.get_tum_aktif_vardiyalar(engine)
                if not df_aktif.empty:
                    son_vardiya = df_aktif.iloc[-1].to_dict()
            if not son_vardiya:
                st.error("Hiç vardiya yok.")
                return

        v_id = int(son_vardiya['id'])
        st.write(f"Vardiya ID: {v_id}")
        
        related = map_db.get_related_vardiya_ids(engine, v_id)
        st.write(f"Birlikte Raporlanacak Makineler: {related}")
        
        html = map_rapor_pdf.uret_is_raporu_html(engine, v_id)
        
        if html:
            st.success("HTML Başarılı!")
            st.components.v1.html(html, height=800, scrolling=True)
        else:
            st.error("HTML Boş Döndü.")

    except Exception as e:
        st.error("HATA OLUŞTU!")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
