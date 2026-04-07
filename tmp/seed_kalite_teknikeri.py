
import sqlite3
import os
import sys
import json
from datetime import datetime

# Path ayarı - Proje kök dizinine göre ayarlandığından emin ol
current_dir = os.path.dirname(os.path.abspath(__file__))
# Proje root dizini
project_root = r"c:\Projeler\S_program\EKLERİSTAN_QMS"
DB_PATH = os.path.join(project_root, "ekleristan_local.db")

def seed_kalite_teknikeri():
    print(f"--- Bağlanılıyor: {DB_PATH} ---")
    if not os.path.exists(DB_PATH):
        print(f"!!! HATA: Veritabanı bulunamadı: {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Foreign Key Desteği
        cursor.execute("PRAGMA foreign_keys = ON")
        
        belge_kodu = "EKL-GK-KAL-002"
        p_id = 1 # MEHMET ÖZGÜR (Sistem Admin)
        
        print(f"--- {belge_kodu} (v4.1.9) Temizlik Yapılıyor... ---")
        
        # SİLME SIRASI: Önce bağımlı tablolar (Child), en son ana tablo (Parent)
        cursor.execute("DELETE FROM qdms_gk_sorumluluklar WHERE belge_kodu = ?", (belge_kodu,))
        cursor.execute("DELETE FROM qdms_gk_etkilesim WHERE belge_kodu = ?", (belge_kodu,))
        cursor.execute("DELETE FROM qdms_gk_periyodik_gorevler WHERE belge_kodu = ?", (belge_kodu,))
        cursor.execute("DELETE FROM qdms_gk_kpi WHERE belge_kodu = ?", (belge_kodu,))
        cursor.execute("DELETE FROM qdms_gorev_karti WHERE belge_kodu = ?", (belge_kodu,))
        cursor.execute("DELETE FROM qdms_belgeler WHERE belge_kodu = ?", (belge_kodu,))

        print(f"--- {belge_kodu} Veriler İşleniyor... ---")
        
        # 1. BELGE KİMLİĞİ (Parent)
        cursor.execute("""
            INSERT INTO qdms_belgeler 
            (belge_kodu, belge_adi, belge_tipi, alt_kategori, durum, aktif_rev, aciklama, olusturan_id, olusturma_tarihi) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (belge_kodu, "Kalite Güvence Teknikeri Görev Tanımı", "GK", "Kalite Güvence", "aktif", 1, 
              "EKLERİSTAN A.Ş. Kalite Güvence Teknikeri Pozisyonu Detaylı Görev Kartı", p_id, '2026-03-27 10:00:00'))

        # 2 & 3 & 5 & 8. POZİSYON PROFİLİ, GÖREV ÖZETİ, YETKİ SINIRLARI, NİTELİKLER
        zorunlu_sertifikalar = json.dumps(["Hijyen Belgesi", "İSG Eğitimi", "Gıda Güvenliği Temel Eğitimi"])
        
        cursor.execute("""
            INSERT INTO qdms_gorev_karti (
                belge_kodu, pozisyon_adi, departman, bagli_pozisyon, vekalet_eden, zone, vardiya_turu, 
                gorev_ozeti, finansal_yetki_tl, imza_yetkisi, vekalet_kosullari, 
                min_egitim, min_deneyim_yil, zorunlu_sertifikalar, tercihli_nitelikler, olusturan_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            belge_kodu, 
            "Kalite Güvence Teknikeri", 
            "Kalite Güvence", 
            "Kalite Güvence Müdürü", 
            "Diğer Kalite Teknikeri veya Kalite Sorumlusu", 
            "Üretim Sahası", 
            "3 Vardiya", 
            "BRCGS v9 / IFS v8 / FSSC 22000 v6 standartları çerçevesinde sahada KKN denetimi yapan sorumludur.", 
            "0", # Finansal Yetki
            "Kalite Kayıtları İmza Yetkisi, Uygunsuzluk Tespitinde Üretim Durdurma Yetkisi", # İmza Yetkisi
            "Mücbir sebeplerde veya yıllık izinlerde Kalite Sorumlusu'na devredilir.", # Vekalet Koşulları
            "Gıda Mühendisi / Teknikeri", 
            1, 
            zorunlu_sertifikalar, 
            "Analitik düşünme yeteneği, MS Office programlarına hakimiyet, BRCGS İç Denetçi sertifikası (Tercihen)",
            p_id
        ))

        # 4. SORUMLULUK ALANLARI (5 Disiplin)
        sorumluluklar = [
            ("personel", "PERSONEL ÜST KRİTER", 1, "Personel hijyen ve KKD kontrollerini gerçekleştirmek.", "BRCGS 1.1.2", "Üretim / İK"),
            ("operasyon", "OPERASYONEL KALİTE", 2, "GMP/GHP denetimi yapmak ve sapmaları raporlamak.", "IFS 4.10", "Üretim / Hijyen"),
            ("gida_guvenligi", "GIDA GÜVENLİĞİ", 3, "KKN ve Operasyonel ÖK ölçüm/kayıtlarını tutmak ve doğrulamak.", "BRCGS 2.0", "Kalite Güvence"),
            ("isg", "İSG UYUM", 4, "Çalışanların KKD kullanımı ve güvenli çalışma denetimi.", "ISO 45001", "İSG Birimi"),
            ("cevre", "ÇEVRESEL YÖNETİM", 5, "Atık ayrıştırma ve su analizi denetimlerini yürütmek.", "ISO 14001", "Çevre Birimi")
        ]
        for tip, kat, sira, icerik, sert, birim in sorumluluklar:
            cursor.execute("""
                INSERT INTO qdms_gk_sorumluluklar (belge_kodu, disiplin_tipi, kategori, sira_no, sorumluluk, sertifikasyon, etkilesim_birimleri)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (belge_kodu, tip, kat, sira, icerik, sert, birim))

        # 6. RACI (Etkileşim)
        etkilesim = [
            ("Üretim", "Proses Kontrol & Yerinde Eğitim", "Sürekli / Sahada", "R/A"),
            ("BT / Yazılım", "QMS Sistem Aksaklıkları", "İhtiyaç Halinde", "R"),
            ("İnsan Kaynakları", "Personel Eğitimi ve Yetkinlik Kayıtları", "Aylık", "A"),
            ("Satın Alma", "Hammadde Uygunsuzluk Bildirimi", "Sürekli", "I")
        ]
        for taraf, konu, siklik, rol in etkilesim:
            cursor.execute("""
                INSERT INTO qdms_gk_etkilesim (belge_kodu, taraf, konu, siklik, raci_rol)
                VALUES (?, ?, ?, ?, ?)
            """, (belge_kodu, taraf, konu, siklik, rol))

        # 7. PERİYODİK GÖREV LİSTESİ
        gorevler = [
            ("KPI Ölçümü (Dolum, Ebat, pH)", "Sürekli", "BRCGS 2.2", "EKL-TL-KAL-001"),
            ("Cam/Sert Plastik Denetimi", "Günlük", "IFS 4.9.3", "EKL-TL-KAL-005"),
            ("Cihaz Doğrulama (Terazi, Termometre)", "Haftalık", "ISO 22000/8", "EKL-TL-KAL-010")
        ]
        for adi, per, sert, tk in gorevler:
            cursor.execute("""
                INSERT INTO qdms_gk_periyodik_gorevler (belge_kodu, gorev_adi, periyot, sertifikasyon_maddesi, talimat_kodu)
                VALUES (?, ?, ?, ?, ?)
            """, (belge_kodu, adi, per, sert, tk))

        # 9. KPI
        kpis = [
            ("Uygunsuzluk Tespit Oranı", "Oran", "Tespit / Toplam Denetim x 100", "Aylık", "Kalite Müdürü"),
            ("KKN Veri Doğruluğu", "%", "100", "Haftalık", "Kalite Müdürü"),
            ("Cihaz Doğrulama Zamanlılığı", "%", "100", "Haftalık", "Kalite Müdürü")
        ]
        for adi, birim, hedef, per, deg in kpis:
            cursor.execute("""
                INSERT INTO qdms_gk_kpi (belge_kodu, kpi_adi, olcum_birimi, hedef_deger, degerlendirme_periyodu, degerlendirici)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (belge_kodu, adi, birim, hedef, per, deg))

        conn.commit()
        print(f"--- BAŞARILI: {belge_kodu} (v4.1.9) migrasyonu Madde 19 kriterlerine göre tamamlandı. ---")

    except Exception as e:
        import traceback
        print(f"!!! KRİTİK HATA !!!")
        print(traceback.format_exc())
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    seed_kalite_teknikeri()
