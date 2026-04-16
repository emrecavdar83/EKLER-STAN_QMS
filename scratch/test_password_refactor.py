import streamlit as st
from logic.auth_logic import sifre_dogrula, sifre_hashle
from logic.security.password import sifre_dogrula as sec_sifre_dogrula
import os

def test_password_refactor():
    print("Testing Password Module Refactor...")
    
    test_pass = "Ekleristan2024!"
    hashed = sifre_hashle(test_pass)
    print(f"Hashed password (via shim): {hashed[:20]}...")
    
    # Verify using shim
    is_valid = sifre_dogrula(test_pass, hashed)
    print(f"Validation via shim: {'SUCCESS' if is_valid else 'FAILURE'}")
    
    # Verify using direct security module
    is_valid_sec = sec_sifre_dogrula(test_pass, hashed)
    print(f"Validation via direct security: {'SUCCESS' if is_valid_sec else 'FAILURE'}")

if __name__ == "__main__":
    test_password_refactor()
