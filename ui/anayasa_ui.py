import streamlit as st
import os

def render_anayasa_module(engine):
    """
    EKLERİSTAN QMS - SİSTEM ANAYASASI (v5.0)
    Projenin 8 katmanlı yapısını ve 30 temel kuralını gösterir.
    """
    st.title("📜 Proje Anayasası")
    st.markdown("---")
    
    anayasa_path = ".antigravity/rules/anayasa.md"
    
    if os.path.exists(anayasa_path):
        with open(anayasa_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Premium Styling Container
        with st.container(border=True):
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
                    <h2 style="color: white; margin: 0;">🏛️ Kurumsal Standartlar ve Etik Kurallar</h2>
                    <p style="opacity: 0.9; margin: 5px 0 0 0;">Anayasa v5.0 | Grand Unification Integrity Seal</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(content, unsafe_allow_html=True)
    else:
        st.error(f"⚠️ Anayasa dosyası bulunamadı: {anayasa_path}")
        st.info("Lütfen sistem yöneticisi ile iletişime geçiniz.")

if __name__ == "__main__":
    from database.connection import get_engine
    render_anayasa_module(get_engine())
