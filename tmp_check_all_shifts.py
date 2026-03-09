import sys
import os
import toml
import pandas as pd
from sqlalchemy import create_engine, text

def list_personnel_shifts():
    # Load secrets
    st_secrets = {}
    try:
        with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
            st_secrets = toml.load(f)
    except Exception as e:
        print(f"Error loading secrets: {e}")
        return

    # Create cloud engine
    db_url = st_secrets.get("database", {}).get("DB_URL")
    if not db_url:
        print("DB_URL not found in secrets.")
        return
        
    engine = create_engine(db_url)
    print("Cloud veritabanına bağlanılıyor...\n")
    
    with engine.connect() as conn:
        try:
            # Vardiyaların Dağılımı Özeti
            print("--- VARDİYA DAĞILIMI (AKTİF PERSONELLER) ---")
            summary_query = """
            SELECT COALESCE(vardiya, 'BOŞ/NULL') as vardiya_turu, COUNT(id) as kisi_sayisi
            FROM personel 
            WHERE durum = 'AKTİF'
            GROUP BY COALESCE(vardiya, 'BOŞ/NULL')
            ORDER BY COUNT(id) DESC
            """
            
            summary_df = pd.read_sql(text(summary_query), conn)
            print(summary_df.to_string(index=False))
            print("\n")

            # Gündüz dahi olmayan, farklı vardiyadaki personeller
            print("--- GÜNDÜZ VARDİYASI DIŞINDAKİ (VEYA BOŞ OLAN) PERSONELLER ---")
            diff_query = """
            SELECT ad_soyad, bolum, vardiya 
            FROM personel 
            WHERE durum = 'AKTİF' AND (vardiya != 'GÜNDÜZ VARDİYASI' OR vardiya IS NULL)
            ORDER BY vardiya, ad_soyad
            """
            diff_df = pd.read_sql(text(diff_query), conn)
            
            if diff_df.empty:
                print("Tüm aktif personeller GÜNDÜZ VARDİYASI'na kayıtlı.")
            else:
                print(diff_df.to_string(index=False))
            
        except Exception as e:
            print(f"Sorgu hatası: {e}")

if __name__ == "__main__":
    list_personnel_shifts()
