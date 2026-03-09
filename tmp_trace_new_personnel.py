import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import text
from database.connection import get_engine
import pandas as pd

def check_new_personnel():
    engine = get_engine()
    print(f"Engine URL: {engine.url}")
    
    with engine.connect() as conn:
        print("\n--- Yeni Eklenen Personeller ---")
        try:
            query = """
            SELECT p.id, p.ad_soyad, p.kullanici_adi, d.bolum_adi, p.vardiya, p.durum 
            FROM personel p 
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id 
            WHERE p.ad_soyad IN ('AYŞEGÜL TETİK', 'ZİLAN ÇİFTÇİ', 'ELİF ÇİFTÇİ', 'MUHAMMED İLKER', 'SONYA TETİK')
            """
            
            df = pd.read_sql(text(query), conn)
            print("DB Verisi:")
            print(df.to_string())
            
            print("\n--- Hijyen Modülü Sorgusu Simülasyonu ---")
            query_hijyen = """
            SELECT p.ad_soyad,
                   COALESCE(d.bolum_adi, 'Tanımsız') as bolum,
                   p.vardiya,
                   p.durum
            FROM personel p
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
            WHERE p.ad_soyad IS NOT NULL
            """
            df_hijyen = pd.read_sql(text(query_hijyen), conn)
            
            df_hijyen.columns = ["Ad_Soyad", "Bolum", "Vardiya", "Durum"]
            if not df_hijyen.empty:
                df_hijyen['Durum'] = df_hijyen['Durum'].astype(str).str.strip().str.upper()
                df_hijyen['Vardiya'] = df_hijyen['Vardiya'].astype(str).str.strip()
                df_hijyen['Bolum'] = df_hijyen['Bolum'].astype(str).str.strip()
                
                # AKTIF filtresi
                df_aktif = df_hijyen[df_hijyen['Durum'] == "AKTİF"]
                print(f"Toplam Aktif Personel: {len(df_aktif)}")
                
                # Yeni personeller listede var mı?
                yeni_isimler = ['AYŞEGÜL TETİK', 'ZİLAN ÇİFTÇİ', 'ELİF ÇİFTÇİ', 'MUHAMMED İLKER', 'SONYA TETİK']
                for isim in yeni_isimler:
                    bulunan = df_aktif[df_aktif['Ad_Soyad'] == isim]
                    if not bulunan.empty:
                        print(f"✅ {isim} Hijyen Listesinde ÇIKIYOR. Bölüm: {bulunan['Bolum'].iloc[0]}, Vardiya: {bulunan['Vardiya'].iloc[0]}")
                    else:
                        print(f"❌ {isim} Hijyen Listesinde ÇIKMIYOR!")
                        # Neden çıkmadığını analiz et
                        ham_bulunan = df_hijyen[df_hijyen['Ad_Soyad'] == isim]
                        if ham_bulunan.empty:
                            print(f"  -> Sebep: Veritabanında (DB) hiç kaydı yok.")
                        else:
                            durum_str = ham_bulunan['Durum'].iloc[0]
                            vardiya_str = ham_bulunan['Vardiya'].iloc[0]
                            print(f"  -> DB'de var ama listeye girmiyor. Durum:'{durum_str}', Vardiya:'{vardiya_str}'")

        except Exception as e:
            print(f"Hata: {e}")

if __name__ == "__main__":
    check_new_personnel()
