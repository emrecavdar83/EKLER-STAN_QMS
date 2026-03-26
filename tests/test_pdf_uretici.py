import sys
import os
from io import BytesIO
import pandas as pd

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.getcwd()))

from modules.qdms.pdf_uretici import org_chart_pdf_uret

def test_pdf_generation():
    print("S2-TESTER: PDF Üretim Testi Başlatılıyor...")
    
    # Mock Veriler
    all_depts = pd.DataFrame([
        {'id': 1, 'bolum_adi': 'GENEL MÜDÜRLÜK', 'ana_departman_id': None},
        {'id': 2, 'bolum_adi': 'KALİTE', 'ana_departman_id': 1},
        {'id': 3, 'bolum_adi': 'ÜRETİM', 'ana_departman_id': 1}
    ])
    
    pers_df = pd.DataFrame([
        {'ad_soyad': 'Test Kişisi', 'departman_id': 2, 'pozisyon_seviye': 1, 'gorev': 'Müdür', 'rol': 'Admin'}
    ])
    
    engine = None # org_chart_pdf_uret şu an engine'i sadece pass ediyor veya query için kullanıyor
    
    try:
        pdf_bytes = org_chart_pdf_uret(engine, all_depts, pers_df)
        if pdf_bytes and len(pdf_bytes) > 0:
            print(f"✅ BAŞARILI: PDF üretildi ({len(pdf_bytes)} byte)")
            return True
        else:
            print("❌ HATALI: PDF boş döndü")
            return False
    except TypeError as e:
        print(f"❌ HATALI: TypeError (Muhtemelen draw_header_footer argüman hatası): {e}")
        return False
    except Exception as e:
        print(f"❌ HATALI: Beklenmedik hata: {e}")
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
