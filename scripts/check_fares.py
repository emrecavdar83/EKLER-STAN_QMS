import pandas as pd
from sqlalchemy import create_engine, text
import os

# Local SQLite bağlantısı (Supabase secrets yok)
engine = create_engine('sqlite:///ekleristan_local.db')

with engine.connect() as conn:
    print("=== FARES YOUNES BİLGİLERİ ===")
    try:
        df = pd.read_sql("SELECT ad_soyad, kullanici_adi, rol, bolum, durum FROM personel WHERE ad_soyad LIKE '%FARES%'", conn)
        if not df.empty:
            print(df.to_string())
        else:
            print("Fares bulunamadı")
    except Exception as e:
        print(f"Hata: {e}")
    
    print("\n=== BÖLÜM SORUMLUSU YETKİLERİ ===")
    try:
        yetki_df = pd.read_sql("SELECT modul_adi, erisim_turu FROM ayarlar_yetkiler WHERE rol_adi = 'Bölüm Sorumlusu'", conn)
        if not yetki_df.empty:
            print(yetki_df.to_string())
        else:
            print("Bölüm Sorumlusu için yetki tanımı bulunamadı (varsayılan davranış aktif)")
    except Exception as e:
        print(f"Yetki tablosu yok veya hata: {e}")
        
    print("\n=== KREMA DEPARTMANINA ATANMIŞ ÜRÜNLER ===")
    try:
        urun_df = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler WHERE sorumlu_departman LIKE '%Krema%' OR sorumlu_departman LIKE '%KREMA%'", conn)
        if not urun_df.empty:
            print(urun_df.to_string())
        else:
            print("Krema departmanına atanmış ürün yok (veya sütun henüz yok)")
    except Exception as e:
        print(f"Ürün sorgusu hatası: {e}")
