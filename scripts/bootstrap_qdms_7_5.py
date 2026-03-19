from sqlalchemy import text
import sys
import os

sys.path.append(os.getcwd())
from database.connection import get_engine

def bootstrap_7_5():
    engine = get_engine()
    print("Aşama 7.5 modülleri kaydediliyor...")
    try:
        with engine.connect() as conn:
            # Modülleri ekle
            conn.execute(text("INSERT OR IGNORE INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif) VALUES ('qdms_talimat', '📖 Talimatlar', 82, 1)"))
            conn.execute(text("INSERT OR IGNORE INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif) VALUES ('qdms_uyumluluk', '✅ Uyumluluk', 83, 1)"))
            
            # Yetkileri ekle
            y_data = [
                ('ADMIN', 'qdms_talimat', 'Düzenle'),
                ('ADMIN', 'qdms_uyumluluk', 'Düzenle'),
                ('KALITE SORUMLUSU', 'qdms_talimat', 'Düzenle'),
                ('KALITE SORUMLUSU', 'qdms_uyumluluk', 'Düzenle'),
                ('OPERATOR', 'qdms_talimat', 'Görüntüle')
            ]
            
            for rol, mod, erisim in y_data:
                conn.execute(text("INSERT OR IGNORE INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (:r, :m, :e)"), {"r": rol, "m": mod, "e": erisim})
            
            conn.commit()
        print("BOOTSTRAP 7.5 SUCCESS")
    except Exception as e:
        print(f"BOOTSTRAP 7.5 FAILED: {str(e)}")

if __name__ == "__main__":
    bootstrap_7_5()
