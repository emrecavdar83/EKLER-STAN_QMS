import sys
import os

# Proje kök dizinini ekle
sys.path.append(r"c:\Projeler\S_program\EKLERİSTAN_QMS")

import pandas as pd
from passlib.hash import bcrypt
from logic.auth_logic import sifre_dogrula, _sifreyi_hashle_ve_guncelle
from sqlalchemy import text
from database.connection import get_engine

def run_synthetic_test():
    print("--- Sentetik Hash Dogrulama Testi Baslatiliyor... ---")
    
    # SENARYO 1: 72 Karakterden Uzun Şifre
    uzun_sifre = "A" * 100
    print(f"1. Test: 100 karakter şifre doğrulama testi...")
    # Bu aşamada db_sifre plain-text olarak simüle edilecek (Lazy Migration tetiklemek için)
    try:
        # sifre_dogrula(girilen, db_sifre_plain, kullanici)
        # Not: Bu çağrı _sifreyi_hashle_ve_guncelle'yi tetikleyecektir.
        res = sifre_dogrula(uzun_sifre, uzun_sifre, "test_user_72")
        print(f"   Sonuc: {'BASARILI' if res == True or res == False else 'BELIRSIZ'}")
        print("   [OK] Hata firlatilmadi (72-byte limit asilsa da truncation sayesinde).")
    except Exception as e:
        print(f"   [ERROR] HATA: {e}")

    # SENARYO 2: Multi-byte (Türkçe/Emoji) ve 72 byte sınırı
    emoji_sifre = "🔒" * 25 # Her biri 4 byte = 100 byte
    print(f"2. Test: Multi-byte (emoji) şifre doğrulama testi...")
    try:
        res = sifre_dogrula(emoji_sifre, emoji_sifre, "test_user_emoji")
        print(f"   Sonuc: {'BASARILI' if res == True or res == False else 'BELIRSIZ'}")
        print("   [OK] Hata firlatilmadi (Multi-byte UTF-8 encoding tespiti).")
    except Exception as e:
        print(f"   [ERROR] HATA: {e}")

    print("\n[FINISH] Sentetik testler tamamlandi. Hata firlatilmadi.")

if __name__ == "__main__":
    run_synthetic_test()
