import streamlit as st

def render_sync_button(key_prefix="global"):
    """Cloud-Primary mimarisinde senkronizasyon butonuna gerek kalmamıştır."""
    st.markdown("---")
    st.info("☁️ **Sistem Cloud-Primary (Bulut Öncelikli) Modda Çalışmaktadır.**")
    st.success("Tüm verileriniz anlık olarak Supabase veritabanına yazılmakta ve okunmaktadır. Çift yönlü senkronizasyon işlemi Anayasa Madde 7 gereği emekliye ayrılmıştır.")

