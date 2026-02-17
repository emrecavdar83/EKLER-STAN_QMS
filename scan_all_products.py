# -*- coding: utf-8 -*-
import pandas as pd
from sqlalchemy import create_engine, text
import toml

# Bağlantı
try:
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
    url = url.strip('"')
    print(f"Connecting to DB...")
    engine = create_engine(url)
except:
    engine = create_engine('sqlite:///ekleristan_local.db')

def check_all_products():
    print("--- TÜM Ürünleri Veri Kontrolü ---")
    
    try:
        df = pd.read_sql("SELECT * FROM ayarlar_urunler", engine)
        if not df.empty:
            print(f"Toplam {len(df)} ürün bulundu.")
            
            error_count = 0
            for idx, row in df.iterrows():
                u_adi = row.get('urun_adi', 'Bilinmiyor')
                
                # Numune Sayısı Kontrolü
                try:
                    ns = float(row.get('numune_sayisi', 0) or 0)
                except ValueError:
                    print(f"⚠️ Hata: '{u_adi}' ürününün 'numune_sayisi' değeri geçersiz: {row.get('numune_sayisi')}")
                    error_count += 1
                
                # Raf Ömrü Kontrolü
                try:
                    ro = float(row.get('raf_omru_gun', 0) or 0)
                except ValueError:
                    print(f"⚠️ Hata: '{u_adi}' ürününün 'raf_omru_gun' değeri geçersiz: {row.get('raf_omru_gun')}")
                    error_count += 1

            if error_count == 0:
                print("✅ Tüm ürün verileri sayısal olarak geçerli görünüyor.")
            else:
                print(f"❌ Toplam {error_count} adet veri hatası bulundu.")
                    
        else:
            print("❌ Hiç ürün bulunamadı!")
            
    except Exception as e:
        print(f"Veritabanı hatası: {e}")

if __name__ == "__main__":
    check_all_products()
