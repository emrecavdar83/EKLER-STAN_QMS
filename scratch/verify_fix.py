import streamlit as st
import sys
from unittest import mock

# Mock engine and session
mock_engine = mock.Mock()

def test_admin_access(role_string):
    print(f"\n--- Testing Role: '{role_string}' ---")
    st.session_state.clear()
    st.session_state.user_rol = role_string
    st.session_state.user = 'TestUser'
    
    # Pre-loading a mock empty yetki_haritasi to simulate DB failure or empty state
    st.session_state.yetki_haritasi = {
        'zones': ['ops'],
        'modules': {'portal': {'erisim': 'goruntule', 'zone': 'ops'}},
        'varsayilan_modul': 'portal'
    }

    from logic.zone_yetki import _normalize_rol, zone_girebilir_mi, modul_gorebilir_mi
    
    norm = _normalize_rol(role_string)
    print(f"Normalized: {norm}")
    
    z_access = zone_girebilir_mi('sys')
    m_access = modul_gorebilir_mi('ayarlar')
    
    print(f"Zone 'sys' access: {z_access}")
    print(f"Module 'ayarlar' access: {m_access}")
    
    if z_access and m_access:
        print("✅ SUCCESS: Admin Bypass Working")
    else:
        print("❌ FAILURE: Admin Access Denied")

if __name__ == "__main__":
    # Simulate various ADMIN strings
    test_cases = ['Admin', 'ADMIN', 'ADMİN', 'admin', 'ADmin ']
    for tc in test_cases:
        test_admin_access(tc)
