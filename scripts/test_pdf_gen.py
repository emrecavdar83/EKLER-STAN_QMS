import sys
import os

# Proje kökünü ekle
sys.path.append(r'c:\Projeler\S_program\EKLERİSTAN_QMS')

from database.connection import get_engine
from modules.qdms.pdf_uretici import pdf_uret
from modules.qdms.sablon_motor import VARSAYILAN_KOLON_CONFIG_SOGUK_ODA

def test_pdf_generation():
    print("Test PDF üretiliyor: EKL-SO-004...")
    
    # 5 Satır Gerçek Ölçüm Verisi
    test_veri = {
        'belge_adi': 'Soğuk Oda İzleme Formu',
        'donem': 'Mart 2026',
        'rev_no': '01',
        'yonu': 'dikey',
        'sablon': {
            'kolon_config': VARSAYILAN_KOLON_CONFIG_SOGUK_ODA
        },
        'satirlar': [
            {'aralik': '00:00-04:00', 'saat': '02:00', 'sicaklik': '3.2', 'durum_badge': 'Uygun', 'personel_tam': 'Ahmet Yılmaz', 'saat_kopya': '02:00'},
            {'aralik': '04:00-08:00', 'saat': '06:15', 'sicaklik': '4.5', 'durum_badge': 'Uygun', 'personel_tam': 'Mehmet Demir', 'saat_kopya': '06:15'},
            {'aralik': '08:00-12:00', 'saat': '10:30', 'sicaklik': '12.0', 'durum_badge': 'Uygunsuz', 'personel_tam': 'Caner Ak', 'saat_kopya': '10:30'},
            {'aralik': '12:00-16:00', 'saat': '14:45', 'sicaklik': '2.8', 'durum_badge': 'Uygun', 'personel_tam': 'Ahmet Yılmaz', 'saat_kopya': '14:45'},
            {'aralik': '16:00-20:00', 'saat': '18:50', 'sicaklik': '3.9', 'durum_badge': 'Uygun', 'personel_tam': 'Mehmet Demir', 'saat_kopya': '18:50'}
        ]
    }
    
    out_path = "test_EKL_SO_004.pdf"
    res_path = pdf_uret(None, "EKL-SO-004", test_veri, out_path)
    
    size_kb = os.path.getsize(res_path) / 1024
    print(f"PDF üretildi: {res_path}")
    print(f"Dosya boyutu: {size_kb:.2f} KB")
    
    if size_kb > 1:
        print("BAŞARILI: PDF boyutu 1KB'den büyük.")
    else:
        print("HATA: PDF boş veya çok küçük!")

if __name__ == "__main__":
    test_pdf_generation()
