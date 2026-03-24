import sys
import os
from database.connection import get_engine
from modules.qdms.pdf_uretici import pdf_uret
from modules.qdms.gk_logic import gk_getir

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.curdir))

engine = get_engine()

def verify_gk_pdf():
    kod = "EKL-KYS-GK-GENEL-MUDUR-001"
    gk_data = gk_getir(engine, kod)
    
    if not gk_data:
        print(f"HATA: {kod} verisi bulunamadı.")
        return
    
    # PDF üreticiye döküman tipini bildir
    gk_data['belge_tipi'] = 'GK'
    
    pdf_path = pdf_uret(engine, kod, gk_data, "tests/gm_gk_test.pdf")
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
        print(f"✓ PDF BAŞARILI: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
    else:
        print("✗ PDF HATASI: Dosya oluşturulamadı veya boş.")

if __name__ == "__main__":
    verify_gk_pdf()
