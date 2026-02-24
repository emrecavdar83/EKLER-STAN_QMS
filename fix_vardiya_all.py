
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def run_fix():
    print("--- Vardiya Düzeltme ve Senkronizasyon Başlatılıyor ---")
    
    # 1. Engines
    local_engine = create_engine('sqlite:///ekleristan_local.db')
    
    try:
        secrets = toml.load('.streamlit/secrets.toml')
        live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
        live_engine = create_engine(live_url)
    except Exception as e:
        print(f"Canlı veritabanı bağlantısı kurulamadı: {e}")
        live_engine = None

    engines = [local_engine]
    if live_engine:
        engines.append(live_engine)

    # 2. Update Queries
    query1 = text("UPDATE personel SET vardiya = 'GÜNDÜZ VARDİYASI' WHERE durum = 'AKTİF'")
    query2 = text("UPDATE personel_vardiya_programi SET vardiya = 'GÜNDÜZ VARDİYASI'")
    
    for eng in engines:
        mode = "LOKAL" if "sqlite" in str(eng.url) else "CANLI"
        print(f"\nİşleniyor: {mode}")
        try:
            with eng.begin() as conn:
                # Personel tablosunu güncelle
                res1 = conn.execute(query1)
                print(f"  - personel tablosu güncellendi ({res1.rowcount} satır)")
                
                # Program tablosunu güncelle (varsa)
                try:
                    res2 = conn.execute(query2)
                    print(f"  - personel_vardiya_programi tablosu güncellendi ({res2.rowcount} satır)")
                except Exception as ex:
                    print(f"  - personel_vardiya_programi tablosu güncellenirken hata (tablo olmayabilir): {ex}")
            print(f"OK: {mode} başarıyla tamamlandı.")
        except Exception as e:
            print(f"HATA: {mode} güncellenirken sorun oluştu: {e}")

    print("\n--- İşlem Tamamlandı ---")

if __name__ == "__main__":
    run_fix()
