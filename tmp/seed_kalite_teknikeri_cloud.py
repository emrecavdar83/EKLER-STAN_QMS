
import sqlalchemy
from sqlalchemy import text
import json
import sys

# Bulut Veritabanı URL'si
DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def seed_kalite_teknikeri_cloud():
    print(f"--- Supabase'e Bağlanılıyor... ---")
    try:
        engine = sqlalchemy.create_engine(DB_URL)
        conn = engine.connect()
        trans = conn.begin()
    except Exception as e:
        print(f"!!! BAĞLANTI HATASI: {e}")
        sys.exit(1)
    
    try:
        belge_kodu = "EKL-GK-KAL-002"
        p_id = 1 # MEHMET ÖZGÜR
        
        print(f"--- {belge_kodu} (v4.1.9) Temizlik ve Migrasyon Başlıyor... ---")
        
        # SİLME SIRASI (Referans bütünlüğü için)
        cursor = conn
        cursor.execute(text("DELETE FROM qdms_gk_sorumluluklar WHERE belge_kodu = :bk"), {"bk": belge_kodu})
        cursor.execute(text("DELETE FROM qdms_gk_etkilesim WHERE belge_kodu = :bk"), {"bk": belge_kodu})
        cursor.execute(text("DELETE FROM qdms_gk_periyodik_gorevler WHERE belge_kodu = :bk"), {"bk": belge_kodu})
        cursor.execute(text("DELETE FROM qdms_gk_kpi WHERE belge_kodu = :bk"), {"bk": belge_kodu})
        cursor.execute(text("DELETE FROM qdms_gorev_karti WHERE belge_kodu = :bk"), {"bk": belge_kodu})
        cursor.execute(text("DELETE FROM qdms_belgeler WHERE belge_kodu = :bk"), {"bk": belge_kodu})

        # 1. BELGE KİMLİĞİ
        cursor.execute(text("""
            INSERT INTO qdms_belgeler 
            (belge_kodu, belge_adi, belge_tipi, alt_kategori, durum, aktif_rev, aciklama, olusturan_id, olusturma_tarihi) 
            VALUES (:bk, :ba, :bt, :ak, :dr, :ar, :ac, :oid, :ot)
        """), {
            "bk": belge_kodu, 
            "ba": "Kalite Güvence Teknikeri Görev Tanımı", 
            "bt": "GK", 
            "ak": "Kalite Güvence", 
            "dr": "aktif", 
            "ar": 1, 
            "ac": "EKLERİSTAN A.Ş. Kalite Güvence Teknikeri Pozisyonu Detaylı Görev Kartı", 
            "oid": p_id, 
            "ot": '2026-03-27 10:00:00'
        })

        # 2 & 3 & 5 & 8. POZİSYON PROFİLİ, GÖREV ÖZETİ, YETKİ SINIRLARI, NİTELİKLER
        zorunlu_sertifikalar = json.dumps(["Hijyen Belgesi", "İSG Eğitimi", "Gıda Güvenliği Temel Eğitimi"])
        
        cursor.execute(text("""
            INSERT INTO qdms_gorev_karti (
                belge_kodu, pozisyon_adi, departman, bagli_pozisyon, vekalet_eden, zone, vardiya_turu, 
                gorev_ozeti, finansal_yetki_tl, imza_yetkisi, vekalet_kosullari, 
                min_egitim, min_deneyim_yil, zorunlu_sertifikalar, tercihli_nitelikler, olusturan_id
            ) VALUES (:bk, :pa, :dp, :bp, :ve, :zn, :vt, :go, :fy, :iy, :vk, :me, :md, :zs, :tn, :oid)
        """), {
            "bk": belge_kodu, 
            "pa": "Kalite Güvence Teknikeri", 
            "dp": "Kalite Güvence", 
            "bp": "Kalite Güvence Müdürü", 
            "ve": "Diğer Kalite Teknikeri veya Kalite Sorumlusu", 
            "zn": "Üretim Sahası", 
            "vt": "3 Vardiya", 
            "go": "BRCGS v9 / IFS v8 / FSSC 22000 v6 standartları çerçevesinde sahada KKN denetimi yapan sorumludur.", 
            "fy": "0", 
            "iy": "Kalite Kayıtları İmza Yetkisi, Uygunsuzluk Tespitinde Üretim Durdurma Yetkisi", 
            "vk": "Mücbir sebeplerde veya yıllık izinlerde Kalite Sorumlusu'na devredilir.", 
            "me": "Gıda Mühendisi / Teknikeri", 
            "md": 1, 
            "zs": zorunlu_sertifikalar, 
            "tn": "Analitik düşünme yeteneği, MS Office programlarına hakimiyet, BRCGS İç Denetçi sertifikası (Tercihen)",
            "oid": p_id
        })

        # 4. SORUMLULUK ALANLARI
        sorumluluklar = [
            ("personel", "PERSONEL ÜST KRİTER", 1, "Personel hijyen ve KKD kontrollerini gerçekleştirmek.", "BRCGS 1.1.2", "Üretim / İK"),
            ("operasyon", "OPERASYONEL KALİTE", 2, "GMP/GHP denetimi yapmak ve sapmaları raporlamak.", "IFS 4.10", "Üretim / Hijyen"),
            ("gida_guvenligi", "GIDA GÜVENLİĞİ", 3, "KKN ve Operasyonel ÖK ölçüm/kayıtlarını tutmak ve doğrulamak.", "BRCGS 2.0", "Kalite Güvence"),
            ("isg", "İSG UYUM", 4, "Çalışanların KKD kullanımı ve güvenli çalışma denetimi.", "ISO 45001", "İSG Birimi"),
            ("cevre", "ÇEVRESEL YÖNETİM", 5, "Atık ayrıştırma ve su analizi denetimlerini yürütmek.", "ISO 14001", "Çevre Birimi")
        ]
        for tip, kat, sira, icerik, sert, birim in sorumluluklar:
            cursor.execute(text("""
                INSERT INTO qdms_gk_sorumluluklar (belge_kodu, disiplin_tipi, kategori, sira_no, sorumluluk, sertifikasyon, etkilesim_birimleri)
                VALUES (:bk, :dt, :kt, :sn, :sr, :st, :eb)
            """), {"bk": belge_kodu, "dt": tip, "kt": kat, "sn": sira, "sr": icerik, "st": sert, "eb": birim})

        # 6. RACI
        etkilesim = [
            ("Üretim", "Proses Kontrol & Yerinde Eğitim", "Sürekli / Sahada", "R/A"),
            ("BT / Yazılım", "QMS Sistem Aksaklıkları", "İhtiyaç Halinde", "R"),
            ("İnsan Kaynakları", "Personel Eğitimi ve Yetkinlik Kayıtları", "Aylık", "A"),
            ("Satın Alma", "Hammadde Uygunsuzluk Bildirimi", "Sürekli", "I")
        ]
        for taraf, konu, siklik, rol in etkilesim:
            cursor.execute(text("""
                INSERT INTO qdms_gk_etkilesim (belge_kodu, taraf, konu, siklik, raci_rol)
                VALUES (:bk, :tf, :kn, :sk, :rr)
            """), {"bk": belge_kodu, "tf": taraf, "kn": konu, "sk": siklik, "rr": rol})

        # 7. PERİYODİK GÖREVLER
        gorevler = [
            ("KPI Ölçümü (Dolum, Ebat, pH)", "Sürekli", "BRCGS 2.2", "EKL-TL-KAL-001"),
            ("Cam/Sert Plastik Denetimi", "Günlük", "IFS 4.9.3", "EKL-TL-KAL-005"),
            ("Cihaz Doğrulama (Terazi, Termometre)", "Haftalık", "ISO 22000/8", "EKL-TL-KAL-010")
        ]
        for adi, per, sert, tk in gorevler:
            cursor.execute(text("""
                INSERT INTO qdms_gk_periyodik_gorevler (belge_kodu, gorev_adi, periyot, sertifikasyon_maddesi, talimat_kodu)
                VALUES (:bk, :ga, :pr, :sm, :tk)
            """), {"bk": belge_kodu, "ga": adi, "pr": per, "sm": sert, "tk": tk})

        # 9. KPI
        kpis = [
            ("Uygunsuzluk Tespit Oranı", "Oran", "Tespit / Toplam Denetim x 100", "Aylık", "Kalite Müdürü"),
            ("KKN Veri Doğruluğu", "%", "100", "Haftalık", "Kalite Müdürü"),
            ("Cihaz Doğrulama Zamanlılığı", "%", "100", "Haftalık", "Kalite Müdürü")
        ]
        for adi, birim, hedef, per, deg in kpis:
            cursor.execute(text("""
                INSERT INTO qdms_gk_kpi (belge_kodu, kpi_adi, olcum_birimi, hedef_deger, degerlendirme_periyodu, degerlendirici)
                VALUES (:bk, :ka, :ob, :hd, :dp, :dg)
            """), {"bk": belge_kodu, "ka": adi, "ob": birim, "hd": hedef, "dp": per, "dg": deg})

        trans.commit()
        print(f"--- BAŞARILI: {belge_kodu} Supabase (Bulut) senkronizasyonu tamamlandı. ---")

    except Exception as e:
        print(f"!!! KRİTİK HATA !!!: {e}")
        trans.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    seed_kalite_teknikeri_cloud()
