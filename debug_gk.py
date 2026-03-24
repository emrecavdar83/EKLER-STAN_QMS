import sys
import os
import traceback
from sqlalchemy import text
from database.connection import get_engine
from modules.qdms.belge_kayit import belge_olustur
from modules.qdms.gk_logic import gk_kaydet, gk_getir

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.curdir))

engine = get_engine()

def debug_gk():
    kod = "EKL-KYS-GK-DEBUG-002"
    try:
        print(f"Testing with code: {kod}")
        # 1. Base Document
        res_b = belge_olustur(engine, kod, "Debug GK v2", "GK", "IK", "Debug", 1)
        print(f"belge_olustur result: {res_b}")
        
        # 2. GK Data
        veri = {
            'belge_kodu': kod,
            'pozisyon_adi': "Debug Pozisyonu",
            'departman': "Debug Dep",
            'gorev_ozeti': "Bu bir SQLAlchemy 2.0 testidir.",
            'olusturan_id': 1,
            'sorumluluklar': [{'kategori': 'genel', 'sira_no': 1, 'sorumluluk': 'Sistem güvenliği'}],
            'periyodik_gorevler': [{'gorev_adi': 'Günlük Yedekleme', 'periyot': 'gunluk'}],
            'kpi_listesi': [],
            'etkilesimler': []
        }
        
        res_gk = gk_kaydet(engine, veri)
        print(f"gk_kaydet result: {res_gk}")
        
        if res_gk['basarili']:
            saved = gk_getir(engine, kod)
            print(f"gk_getir result: Pozisyon={saved['pozisyon_adi']}, Sorumluluklar={len(saved['sorumluluklar'])}")
            if saved['pozisyon_adi'] == "Debug Pozisyonu":
                print("✓ TEST BAŞARILI: GK Verisi kaydedildi ve geri okundu.")
        
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    debug_gk()
