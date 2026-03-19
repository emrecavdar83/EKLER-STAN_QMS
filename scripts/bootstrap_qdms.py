import sys
import os
from sqlalchemy import create_engine

# Proje kökünü ekle
sys.path.append(r'c:\Projeler\S_program\EKLERİSTAN_QMS')

from database.schema_qdms import init_qdms_tables
from modules.qdms.belge_kayit import belge_olustur, belge_durum_guncelle
from modules.qdms.sablon_motor import sablon_kaydet, VARSAYILAN_HEADER_CONFIG, VARSAYILAN_KOLON_CONFIG_SOGUK_ODA

def bootstrap():
    # Yerel veritabanına doğrudan bağlan (Streamlit secrets bağımlılığını bypass et)
    db_url = 'sqlite:///ekleristan_local.db'
    engine = create_engine(db_url)
    
    # Şemayı garanti et
    print("Şema kontrol ediliyor...")
    init_qdms_tables(engine)
    
    # 1. Belge oluştur
    print("Belge oluşturuluyor: EKL-SO-004...")
    res = belge_olustur(
        engine, 
        "EKL-SO-004", 
        "Soğuk Oda İzleme Formu", 
        "form", 
        "soguk_oda", 
        "Soğuk odaların periyodik sıcaklık takibi için temel form.",
        1 # Admin ID
    )
    print(f"Sonuç: {res}")
    
    # 2. Durumu aktif yap
    print("Durum güncelleniyor: aktif...")
    belge_durum_guncelle(engine, "EKL-SO-004", "incelemede", 1)
    belge_durum_guncelle(engine, "EKL-SO-004", "aktif", 1)
    
    # 3. Şablon kaydet
    print("Şablon kaydediliyor...")
    s_res = sablon_kaydet(
        engine,
        "EKL-SO-004",
        1, # Revize 1
        VARSAYILAN_HEADER_CONFIG,
        VARSAYILAN_KOLON_CONFIG_SOGUK_ODA,
        {"taraf": "Kalite"},
        sayfa_boyutu="A4",
        sayfa_yonu="dikey"
    )
    print(f"Şablon Sonuç: {s_res}")

if __name__ == "__main__":
    bootstrap()
