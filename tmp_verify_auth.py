import sys
import os

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

# Streamlit session state mock
import streamlit as st
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True
    st.session_state.user_rol = 'BÖLÜM SORUMLUSU'

from logic.auth_logic import kullanici_yetkisi_var_mi

def test_auth():
    print("--- Yetki Testi ---")
    view_ok = kullanici_yetkisi_var_mi("❄️ Soğuk Oda Sıcaklıkları", "Görüntüle")
    edit_ok = kullanici_yetkisi_var_mi("❄️ Soğuk Oda Sıcaklıkları", "Düzenle")
    
    print(f"Modül: ❄️ Soğuk Oda Sıcaklıkları")
    print(f"Rol: BÖLÜM SORUMLUSU")
    print(f"Görüntüleme Yetkisi: {view_ok}")
    print(f"Düzenleme Yetkisi: {edit_ok}")
    
    if view_ok and edit_ok:
        print("SONUÇ: BAŞARILI")
    else:
        print("SONUÇ: BAŞARISIZ")

if __name__ == "__main__":
    test_auth()
