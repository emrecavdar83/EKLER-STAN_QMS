import sys
import os
from database.connection import get_engine
from modules.qdms.belge_kayit import belge_olustur
from modules.qdms.gk_logic import gk_kaydet

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.curdir))

engine = get_engine()

def create_genel_mudur_gk():
    kod = "EKL-KYS-GK-GENEL-MUDUR-001"
    
    # 1. Base Document
    belge_olustur(engine, kod, "Genel Müdür Görev Kartı", "GK", "Yönetim", "Ekleristan Genel Müdür pozisyon tanımı.", 1)
    
    # 2. GK Data
    veri = {
        'belge_kodu': kod,
        'pozisyon_adi': "Genel Müdür",
        'departman': "Genel Müdürlük",
        'bagli_pozisyon': "Yönetim Kurulu",
        'vekalet_eden': "İşletme Müdürü",
        'zone': "mgt",
        'vardiya_turu': "Hafta içi 08:30 - 18:00",
        'gorev_ozeti': "Şirketin tüm operasyonel ve stratejik süreçlerini BRCGS/IFS standartlarına uygun şekilde yönetmek.",
        'finansal_yetki_tl': 500000.0,
        'imza_yetkisi': "Birinci Derece İmza Yetkisi",
        'min_egitim': "Lisans / Yüksek Lisans",
        'min_deneyim_yil': 10,
        'olusturan_id': 1,
        'sorumluluklar': [
            {'kategori': 'genel', 'sira_no': 1, 'sorumluluk': 'Stratejik hedeflerin belirlenmesi'},
            {'kategori': 'gida_guvenligi', 'sira_no': 2, 'sorumluluk': 'Gıda güvenliği kültürünün yaygınlaştırılması'},
            {'kategori': 'isg', 'sira_no': 3, 'sorumluluk': 'İş sağlığı ve güvenliği kurallarına uyulmasını temin etmek'}
        ],
        'periyodik_gorevler': [
            {'gorev_adi': 'Yönetimin Gözden Geçirme Toplantısı', 'periyot': 'yillik', 'sertifikasyon_maddesi': 'BRC 1.1'},
            {'gorev_adi': 'Haftalık Koordinasyon Toplantısı', 'periyot': 'haftalik'}
        ],
        'etkilesimler': [
            {'taraf': 'Yönetim Kurulu', 'konu': 'Bütçe Onayı', 'siklik': 'Yıllık', 'raci_rol': 'A'}
        ],
        'kpi_listesi': [
            {'kpi_adi': 'Yıllık Büyüme Oranı', 'olcum_birimi': '%', 'hedef_deger': 20.0, 'degerlendirme_periyodu': 'Yıllık', 'degerlendirici': 'Yönetim Kurulu'}
        ]
    }
    
    res = gk_kaydet(engine, veri)
    if res['basarili']:
        print(f"BAŞARILI: {kod} oluşturuldu.")
    else:
        print(f"HATA: {res['hata']}")

if __name__ == "__main__":
    create_genel_mudur_gk()
