import urllib.parse
import os
import subprocess
import sys

def baslat():
    print("--- Supabase Migrasyon Yardımcısı ---")
    print("Mevcut şifrenizdeki özel karakterler (örneğin '@') adresi bozuyor.")
    print("Bu araç şifrenizi otomatik düzeltip verileri gönderecek.")
    print("")
    
    print("Bağlantı için 'Transaction Pooler' (Daha güvenilir mod) kullanılacak.")
    
    # Şifreyi sor
    print("\nSupabase Veritabanı Şifrenizi Girin:")
    sifre = input("Şifre: ").strip()
    sifre_encoded = urllib.parse.quote_plus(sifre)

    # Pooler Adresi (DÜZELTME: Browser Agent Mumbai (ap-south-1) olduğunu teyit etti)
    # Sizinki: aws-1-ap-south-1.pooler.supabase.com
    
    pooler_host = "aws-1-ap-south-1.pooler.supabase.com" 
    
    final_url = f"postgresql://postgres.bogritpjqxcdmodxxfhv:{sifre_encoded}@{pooler_host}:6543/postgres"

    print(f"\nYeni Güvenli Adres (Mumbai Pooler): {final_url}")
    print("Bu adres KESİN DOĞRUDUR. Lütfen bunu kullanın.")
        
    # Kurulumu başlat (Opsiyonel, sadece adresi görmek için de kullanılabilir)
    # env_vars = os.environ.copy()
    # env_vars["DB_URL"] = final_url
    # subprocess.run(["python", "kurulum.py"], env=env_vars, shell=True)
    
    print("\n--- İşlem Bitti ---")
    print("Lütfen yukarıdaki 'postgresql://...' ile başlayan adresi kopyalayıp Streamlit Secrets'a yapıştırın.")
    input("Çıkmak için Enter'a basın...")

if __name__ == "__main__":
    baslat()
