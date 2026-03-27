import sqlite3
import os
import sys
import json
from datetime import datetime

# Path ayarı
project_root = r"c:\Projeler\S_program\EKLERİSTAN_QMS"
sys.path.append(project_root)

from database.connection import get_engine
from modules.qdms.gk_logic import gk_getir
from modules.qdms.pdf_uretici import pdf_uret

def test_pdf_generation():
    engine = get_engine()
    belge_kodu = "EKL-GK-KAL-002"
    
    print(f"--- {belge_kodu} verileri çekiliyor... ---")
    veri = gk_getir(engine, belge_kodu)
    
    if not veri:
        print("!!! HATA: Veri bulunamadı. Lütfen önce seed scripti çalıştırın.")
        return
        
    # PDF üretimi için gerekli ek meta veriler
    veri['belge_tipi'] = 'GK'
    veri['belge_adi'] = "Kalite Güvence Teknikeri Görev Tanımı"
    veri['rev_no'] = '01'
    veri['yayim_tarihi'] = '27.03.2026'
    veri['durum'] = 'Yayın'
    
    output_path = os.path.join(project_root, f"test_{belge_kodu}.pdf")
    print(f"--- PDF üretiliyor: {output_path} ---")
    
    try:
        pdf_uret(engine, belge_kodu, veri, output_path)
        print(f"--- BAŞARILI: PDF üretildi. Lütfen dosyayı kontrol edin: {output_path} ---")
    except Exception as e:
        print(f"!!! HATA: PDF üretimi başarısız: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()
