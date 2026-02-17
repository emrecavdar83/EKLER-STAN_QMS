import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///ekleristan_local.db')

with engine.connect() as conn:
    print("=== DİLEK ATAK KAYDI ===")
    try:
        df = pd.read_sql("SELECT ad_soyad, kullanici_adi, sifre, rol, bolum, durum FROM personel WHERE ad_soyad LIKE '%DILEK%' OR ad_soyad LIKE '%Dilek%' OR ad_soyad LIKE '%DİLEK%'", conn)
        if not df.empty:
            print(df.to_string())
        else:
            print("Dilek Atak bulunamadı")
    except Exception as e:
        print(f"Hata: {e}")
    
    print("\n=== GİRİŞ EKRANINDA GÖRÜNEN TÜM KULLANICILAR ===")
    try:
        users_df = pd.read_sql("SELECT kullanici_adi FROM personel WHERE kullanici_adi IS NOT NULL", conn)
        print(users_df['kullanici_adi'].tolist())
    except Exception as e:
        print(f"Hata: {e}")
