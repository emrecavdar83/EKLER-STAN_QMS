import urllib.parse
import os
import subprocess
import sys

def baslat():
    print("--- Supabase Migrasyon Yardımcısı ---")
    print("Mevcut şifrenizdeki özel karakterler (örneğin '@') adresi bozuyor.")
    print("Bu araç şifrenizi otomatik düzeltip verileri gönderecek.")
    print("")
    
    # Adresi doğrudan kullanıcıdan al
    print("Supabase'deki 'Connection String'i kopyalayın.")
    print("ÖNEMLİ: Adres içinde '[YOUR-PASSWORD]' yazısı olduğundan emin olun.")
    full_uri = input("URI: ").strip()
    
    # Şifreyi ayrıca sor
    print("\nŞifrenizi girin:")
    sifre = input("Şifre: ").strip()
    sifre_encoded = urllib.parse.quote_plus(sifre)

    # Basitçe placeholder'ı değiştir
    if "[YOUR-PASSWORD]" in full_uri:
        final_url = full_uri.replace("[YOUR-PASSWORD]", sifre_encoded)
        print(f"\nAdres Hazırlandı, Bağlanılıyor...")
        
        # Kurulumu başlat
        env_vars = os.environ.copy()
        env_vars["DB_URL"] = final_url
        subprocess.run(["python", "kurulum.py"], env=env_vars, shell=True)
    else:
        print("\nHATA: Yapıştırdığınız adreste '[YOUR-PASSWORD]' yazısı bulunamadı.")
        print("Lütfen Supabase'den adresi tekrar kopyalayın (şifreyi elle değiştirmeden).")

    print("\n--- İşlem Bitti ---")
    input("Çıkmak için Enter'a basın...")

if __name__ == "__main__":
    baslat()
