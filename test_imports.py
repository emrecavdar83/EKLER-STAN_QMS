import sys
import os

print("Starting deep import check...")

try:
    from modules.qdms.belge_kayit import belge_olustur, belge_listele, belge_durum_guncelle, belge_getir, belge_guncelle, belge_kodu_oner
    print("[OK] modules.qdms.belge_kayit")
except Exception as e:
    print(f"[FAIL] modules.qdms.belge_kayit: {e}")

try:
    from modules.qdms.revizyon import revizyon_gecmisi_getir, revizyon_baslat
    print("[OK] modules.qdms.revizyon")
except Exception as e:
    print(f"[FAIL] modules.qdms.revizyon: {e}")

try:
    from modules.qdms.pdf_uretici import pdf_uret
    print("[OK] modules.qdms.pdf_uretici")
except Exception as e:
    print(f"[FAIL] modules.qdms.pdf_uretici: {e}")

try:
    from modules.qdms.sablon_motor import sablon_getir, sablon_kaydet, sablon_guncelle
    print("[OK] modules.qdms.sablon_motor")
except Exception as e:
    print(f"[FAIL] modules.qdms.sablon_motor: {e}")

try:
    from modules.qdms.talimat_yonetici import talimat_olustur, talimat_guncelle, talimat_getir_by_kod, okunmayan_talimatlar, okuma_onay_kaydet
    print("[OK] modules.qdms.talimat_yonetici")
except Exception as e:
    print(f"[FAIL] modules.qdms.talimat_yonetici: {e}")

try:
    from modules.qdms.uyumluluk_rapor import uyumluluk_ozeti_getir
    print("[OK] modules.qdms.uyumluluk_rapor")
except Exception as e:
    print(f"[FAIL] modules.qdms.uyumluluk_rapor: {e}")

print("Deep check finished.")
